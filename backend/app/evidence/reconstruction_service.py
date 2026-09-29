"""Orchestrator for incident candidate reconstruction and temporal event segmentation.

Coordinates:
    Synchronized Telemetry (25Hz SI grid)
        ↓
    Pairwise Feature Extraction (kinematics, accelerations, normal-racing filters)
        ↓
    Multi-Signal Candidate Detection (spatial + kinematic + vehicle response)
        ↓
    Temporal Segmentation & Merging (pre/post padding, peak identification)
        ↓
    Contextual Race Control Correlation (FIA flags and messages)
        ↓
    Candidate Dossier Construction (neutral empirical evidence, quality flags)
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.logging import logger
from app.evidence.association import (
    extract_race_control_context,
    get_session_race_control_messages,
)
from app.evidence.candidate import (
    CandidateBatchResponse,
    CandidateDossier,
    CandidateQueryRequest,
)
from app.evidence.detector import DetectorConfig, MultiSignalDetector
from app.evidence.dossier import (
    IncidentEvidenceDossier,
    synthesize_incident_evidence_dossier,
)
from app.evidence.event_builder import build_candidate_dossier
from app.evidence.features import extract_pairwise_features
from app.evidence.segmenter import EpisodeSegmenter, SegmenterConfig
from app.evidence.video_evidence import VideoSourceMetadata
from app.schemas.telemetry import TelemetryPointSchema
from app.services.ingestion_service import get_ingestion_service
from app.services.telemetry_service import get_telemetry_service, synchronize_pair


class IncidentReconstructionEngine:
    """Deterministic, multi-signal evidence extraction and candidate reconstruction engine."""

    def __init__(
        self,
        detector_config: Optional[DetectorConfig] = None,
        segmenter_config: Optional[SegmenterConfig] = None,
    ):
        self.detector = MultiSignalDetector(config=detector_config)
        self.segmenter = EpisodeSegmenter(config=segmenter_config)
        self.telemetry_service = get_telemetry_service()
        self.ingestion = get_ingestion_service()
        self._candidate_cache: Dict[str, Tuple[CandidateDossier, List[TelemetryPointSchema], List[Any], List[Dict[str, Any]]]] = {}

    def reconstruct_pair_candidates(
        self,
        season: int,
        round_or_name: Union[int, str],
        session_identifier: str,
        driver_a: str,
        driver_b: str,
        lap: Optional[int] = None,
        frequency_hz: float = 25.0,
        session_rcm: Optional[List[Dict[str, Any]]] = None,
    ) -> List[CandidateDossier]:
        """Reconstruct candidate events for a specific driver pair across a lap or window."""
        drv_a = driver_a.upper()
        drv_b = driver_b.upper()
        session_id = f"f1-{season}-{str(round_or_name).lower()}-{session_identifier.lower()}"

        # 1. Load raw telemetry points
        raw_a = self.ingestion.load_driver_telemetry(
            season=season,
            round_or_name=round_or_name,
            session_identifier=session_identifier,
            driver=drv_a,
            lap=lap,
        )
        raw_b = self.ingestion.load_driver_telemetry(
            season=season,
            round_or_name=round_or_name,
            session_identifier=session_identifier,
            driver=drv_b,
            lap=lap,
        )

        if not raw_a or not raw_b:
            logger.info(f"Insufficient raw telemetry for {drv_a} or {drv_b}")
            return []

        # 2. Synchronize onto 25 Hz SI grid
        dt_sec = 1.0 / frequency_hz
        synced_frames = synchronize_pair(raw_a, raw_b, frequency_hz=frequency_hz)
        if len(synced_frames) < 10:
            return []

        # 3. Extract multi-channel features
        features = extract_pairwise_features(synced_frames, dt_sec=dt_sec)

        # 4. Multi-signal candidate detection
        triggered_frames = self.detector.detect_candidate_frames(features)
        if not triggered_frames:
            return []

        # 5. Temporal segmentation & event merging
        episodes = self.segmenter.segment_triggers(
            triggered_frames=triggered_frames,
            all_features=features,
            dt_sec=dt_sec,
        )
        if not episodes:
            return []

        # 6. Race control message correlation
        if session_rcm is None:
            session_rcm = get_session_race_control_messages(
                season=season, round_or_name=str(round_or_name), session_identifier=session_identifier
            )

        # 7. Dossier construction
        candidates: List[CandidateDossier] = []
        for i, ep in enumerate(episodes):
            cand_id = f"CAND-{season}-{str(round_or_name).upper()[:3]}-{drv_a}_{drv_b}-L{lap or 'X'}-{i+1:02d}"
            rcm_context = extract_race_control_context(ep, drv_a, drv_b, session_rcm)

            dossier = build_candidate_dossier(
                candidate_id=cand_id,
                session_id=session_id,
                episode=ep,
                driver_a=drv_a,
                driver_b=drv_b,
                raw_frames=synced_frames,
                race_control_messages=rcm_context,
            )
            candidates.append(dossier)
            self._candidate_cache[cand_id] = (dossier, synced_frames, features, session_rcm or [])

        return candidates

    def analyze_session_scope(
        self,
        request: CandidateQueryRequest,
    ) -> CandidateBatchResponse:
        """Execute bounded candidate extraction across specified pairs or session scope."""
        t0 = time.time()
        session_id = f"f1-{request.season}-{str(request.round_or_name).lower()}-{request.session.lower()}"

        # Determine target driver pairs
        pairs_to_evaluate: List[Tuple[str, str]] = []
        if request.driver_a and request.driver_b:
            pairs_to_evaluate.append((request.driver_a, request.driver_b))
        elif request.driver_a:
            # Pair focal driver against key rivals in session
            drivers = self.ingestion.load_session_drivers(
                request.season, request.round_or_name, request.session
            )
            rivals = [d.code for d in drivers if d.code != request.driver_a.upper()]
            pairs_to_evaluate.extend((request.driver_a.upper(), riv) for riv in rivals[:5])
        else:
            # Default evaluation pairings
            pairs_to_evaluate = [
                ("RIC", "HUL"),
                ("HUL", "TSU"),
                ("MAG", "GAS"),
                ("LEC", "SAI"),
                ("VER", "NOR"),
            ]

        # Load session race control messages once
        session_rcm = get_session_race_control_messages(
            season=request.season,
            round_or_name=request.round_or_name,
            session_identifier=request.session,
        )

        all_candidates: List[CandidateDossier] = []

        for drv_a, drv_b in pairs_to_evaluate:
            try:
                cands = self.reconstruct_pair_candidates(
                    season=request.season,
                    round_or_name=request.round_or_name,
                    session_identifier=request.session,
                    driver_a=drv_a,
                    driver_b=drv_b,
                    lap=request.lap,
                    session_rcm=session_rcm,
                )
                all_candidates.extend(cands)
            except Exception as e:
                logger.warning(f"Error evaluating pair {drv_a} vs {drv_b}: {e}")

        # Enforce safety cap on returned candidates
        capped_candidates = all_candidates[: request.limit]
        elapsed = round(time.time() - t0, 3)

        return CandidateBatchResponse(
            session_id=session_id,
            total_candidates=len(capped_candidates),
            processing_time_sec=elapsed,
            candidates=capped_candidates,
        )

    def get_candidate_dossier(
        self,
        candidate_id: str,
        video_source: Optional[VideoSourceMetadata] = None,
    ) -> Optional[IncidentEvidenceDossier]:
        """Retrieve or reconstruct the full multi-modal IncidentEvidenceDossier for a candidate."""
        # 1. Check direct in-memory cache
        if candidate_id in self._candidate_cache:
            cand, raw_frames, features, rcm = self._candidate_cache[candidate_id]
            return synthesize_incident_evidence_dossier(
                candidate=cand,
                raw_frames=raw_frames,
                all_features=features,
                session_rcm=rcm,
                video_source=video_source,
            )

        # 2. Check known reference cases (e.g. REF-MONZA-01 -> RIC_HUL Lap 1)
        ref_map = {
            "REF-MONZA-01": (2024, "Italian Grand Prix", "Race", "RIC", "HUL", 1),
            "REF-MONZA-02": (2024, "Italian Grand Prix", "Race", "HUL", "TSU", 4),
            "REF-MONZA-03": (2024, "Italian Grand Prix", "Race", "MAG", "GAS", 19),
        }

        if candidate_id in ref_map:
            season, round_name, sess, drv_a, drv_b, lap_val = ref_map[candidate_id]
            cands = self.reconstruct_pair_candidates(
                season=season,
                round_or_name=round_name,
                session_identifier=sess,
                driver_a=drv_a,
                driver_b=drv_b,
                lap=lap_val,
            )
            if cands and cands[0].candidate_id in self._candidate_cache:
                cand, raw_frames, features, rcm = self._candidate_cache[cands[0].candidate_id]
                res_dossier = synthesize_incident_evidence_dossier(
                    candidate=cand,
                    raw_frames=raw_frames,
                    all_features=features,
                    session_rcm=rcm,
                    video_source=video_source,
                )
                res_dossier.candidate_id = candidate_id
                return res_dossier

        # 3. Parse pattern CAND-{season}-{round}-{drv_a}_{drv_b}-L{lap}-{idx}
        m = re.match(r"CAND-(\d{4})-([A-Z0-9]+)-([A-Z0-9]+)_([A-Z0-9]+)-L(\d+|X)-(\d+)", candidate_id)
        if m:
            season = int(m.group(1))
            round_code = m.group(2)
            round_name = "Italian Grand Prix" if round_code in ("MON", "ITA") else round_code
            drv_a = m.group(3)
            drv_b = m.group(4)
            lap_val = int(m.group(5)) if m.group(5) != "X" else None
            cands = self.reconstruct_pair_candidates(
                season=season,
                round_or_name=round_name,
                session_identifier="Race",
                driver_a=drv_a,
                driver_b=drv_b,
                lap=lap_val,
            )
            if candidate_id in self._candidate_cache:
                cand, raw_frames, features, rcm = self._candidate_cache[candidate_id]
                return synthesize_incident_evidence_dossier(
                    candidate=cand,
                    raw_frames=raw_frames,
                    all_features=features,
                    session_rcm=rcm,
                    video_source=video_source,
                )
            elif cands:
                cand, raw_frames, features, rcm = self._candidate_cache[cands[0].candidate_id]
                return synthesize_incident_evidence_dossier(
                    candidate=cand,
                    raw_frames=raw_frames,
                    all_features=features,
                    session_rcm=rcm,
                    video_source=video_source,
                )

        return None



_engine_instance: Optional[IncidentReconstructionEngine] = None


def get_reconstruction_engine() -> IncidentReconstructionEngine:
    """Singleton accessor for IncidentReconstructionEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = IncidentReconstructionEngine()
    return _engine_instance
