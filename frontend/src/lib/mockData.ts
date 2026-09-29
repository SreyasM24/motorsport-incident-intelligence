import { 
  Driver, 
  Incident, 
  Race, 
  TelemetryPoint, 
  RelevantRegulation,
  AssistantMessage
} from './types';

export const MOCK_DRIVERS: Record<string, Driver> = {
  VER: {
    code: 'VER',
    number: 1,
    name: 'Max Verstappen',
    team: 'Red Bull Racing',
    teamColor: '#3671C6',
    secondaryColor: '#E10600',
    country: 'NED',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 246.4,
      maxSpeedKmh: 351.2,
      incidentsInvolved: 2,
      interactionsDetected: 41,
    },
  },
  HAM: {
    code: 'HAM',
    number: 44,
    name: 'Lewis Hamilton',
    team: 'Mercedes-AMG Petronas',
    teamColor: '#00D2BE',
    secondaryColor: '#E0E0E0',
    country: 'GBR',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 245.8,
      maxSpeedKmh: 349.6,
      incidentsInvolved: 2,
      interactionsDetected: 38,
    },
  },
  NOR: {
    code: 'NOR',
    number: 4,
    name: 'Lando Norris',
    team: 'McLaren F1 Team',
    teamColor: '#FF8000',
    secondaryColor: '#000000',
    country: 'GBR',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 247.1,
      maxSpeedKmh: 352.4,
      incidentsInvolved: 1,
      interactionsDetected: 32,
    },
  },
  PIA: {
    code: 'PIA',
    number: 81,
    name: 'Oscar Piastri',
    team: 'McLaren F1 Team',
    teamColor: '#FF8000',
    secondaryColor: '#47C7FC',
    country: 'AUS',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 246.9,
      maxSpeedKmh: 351.8,
      incidentsInvolved: 1,
      interactionsDetected: 35,
    },
  },
  LEC: {
    code: 'LEC',
    number: 16,
    name: 'Charles Leclerc',
    team: 'Scuderia Ferrari HP',
    teamColor: '#E80020',
    secondaryColor: '#FFF200',
    country: 'MON',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 247.8,
      maxSpeedKmh: 354.1,
      incidentsInvolved: 1,
      interactionsDetected: 29,
    },
  },
  SAI: {
    code: 'SAI',
    number: 55,
    name: 'Carlos Sainz',
    team: 'Scuderia Ferrari HP',
    teamColor: '#E80020',
    secondaryColor: '#000000',
    country: 'ESP',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 246.2,
      maxSpeedKmh: 350.5,
      incidentsInvolved: 1,
      interactionsDetected: 27,
    },
  },
  RUS: {
    code: 'RUS',
    number: 63,
    name: 'George Russell',
    team: 'Mercedes-AMG Petronas',
    teamColor: '#00D2BE',
    secondaryColor: '#1E1E1E',
    country: 'GBR',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 245.1,
      maxSpeedKmh: 348.7,
      incidentsInvolved: 1,
      interactionsDetected: 34,
    },
  },
  PER: {
    code: 'PER',
    number: 11,
    name: 'Sergio Perez',
    team: 'Red Bull Racing',
    teamColor: '#3671C6',
    secondaryColor: '#FFCC00',
    country: 'MEX',
    stats: {
      lapsCompleted: 53,
      avgSpeedKmh: 244.7,
      maxSpeedKmh: 349.1,
      incidentsInvolved: 1,
      interactionsDetected: 44,
    },
  },
};

export const MOCK_RACES: Race[] = [
  {
    id: 'ita-2024',
    name: 'Italian Grand Prix',
    circuit: 'Autodromo Nazionale Monza',
    country: 'Italy',
    season: '2024',
    year: 2024,
    sessionType: 'Race',
    date: '2024-09-01',
    driversCount: 20,
    candidatesCount: 1298,
    confirmedCount: 4,
    reviewCount: 3,
    status: 'ANALYSIS READY',
    telemetryAvailable: true,
    videoAvailable: true,
    regulationSet: 'FIA Sporting Regulations 2024 v4',
  },
  {
    id: 'gbr-2024',
    name: 'British Grand Prix',
    circuit: 'Silverstone Circuit',
    country: 'United Kingdom',
    season: '2024',
    year: 2024,
    sessionType: 'Race',
    date: '2024-07-07',
    driversCount: 20,
    candidatesCount: 1412,
    confirmedCount: 6,
    reviewCount: 2,
    status: 'ANALYSIS READY',
    telemetryAvailable: true,
    videoAvailable: true,
    regulationSet: 'FIA Sporting Regulations 2024 v3',
  },
  {
    id: 'bel-2024',
    name: 'Belgian Grand Prix',
    circuit: 'Circuit de Spa-Francorchamps',
    country: 'Belgium',
    season: '2024',
    year: 2024,
    sessionType: 'Race',
    date: '2024-07-28',
    driversCount: 20,
    candidatesCount: 1150,
    confirmedCount: 3,
    reviewCount: 1,
    status: 'ANALYSIS READY',
    telemetryAvailable: true,
    videoAvailable: false,
    regulationSet: 'FIA Sporting Regulations 2024 v3',
  },
  {
    id: 'mon-2024',
    name: 'Monaco Grand Prix',
    circuit: 'Circuit de Monaco',
    country: 'Monaco',
    season: '2024',
    year: 2024,
    sessionType: 'Race',
    date: '2024-05-26',
    driversCount: 20,
    candidatesCount: 840,
    confirmedCount: 5,
    reviewCount: 0,
    status: 'ANALYSIS READY',
    telemetryAvailable: true,
    videoAvailable: true,
    regulationSet: 'FIA Sporting Regulations 2024 v2',
  },
  {
    id: 'abu-2024',
    name: 'Abu Dhabi Grand Prix',
    circuit: 'Yas Marina Circuit',
    country: 'UAE',
    season: '2024',
    year: 2024,
    sessionType: 'Race',
    date: '2024-12-08',
    driversCount: 20,
    candidatesCount: 960,
    confirmedCount: 2,
    reviewCount: 1,
    status: 'ANALYSIS READY',
    telemetryAvailable: true,
    videoAvailable: true,
    regulationSet: 'FIA Sporting Regulations 2024 v5',
  },
];

export const MOCK_INCIDENTS: Incident[] = [
  {
    id: 'INC-024',
    session: 'Italian Grand Prix 2024 — Race',
    raceId: 'ita-2024',
    circuit: 'Monza',
    lap: 31,
    turn: 'Turn 4 (Variante della Roggia)',
    timestamp: '13:42:18.4',
    timeWindow: {
      start: '13:42:16.0',
      end: '13:42:21.0',
    },
    driverA: 'VER',
    driverB: 'HAM',
    incidentType: 'Possible Contact / Vehicle Disturbance',
    confidence: 87,
    status: 'REQUIRES_REVIEW',
    severity: 'HIGH',
    summary:
      'Telemetry indicates a close interaction followed by significant relative motion and a vehicle response. Additional visual evidence is recommended before drawing a final conclusion.',
    detectionMethod: 'Telemetry + relative motion (FastF1 & IMU derivative)',
    videoAvailable: true,
    videoPath: '/assets/this-is-formula-one.mp4',
    telemetryAvailable: true,
    regulationsAvailable: true,
    sources: {
      telemetry: 'FastF1 ECU CAN-Bus + GPS 25Hz',
      video: 'World Feed T4 Onboard (Linked / Available)',
      regulations: 'FIA Formula One Sporting Regulations 2024 (Art 33.4)',
    },
    evidenceAssessment: [
      {
        id: 'ev-1',
        category: 'PROXIMITY',
        title: 'Minimum Lateral Proximity',
        observedValue: '1.82 m',
        expectedContext: 'Typical apex margin: 2.80 m – 3.40 m at Roggia chicane',
        confidence: 92,
        source: 'GPS Positioning + Optical Track Geometry',
        description: 'Cars reached minimum measured clearance at apex initiation of Turn 4.',
        verified: true,
      },
      {
        id: 'ev-2',
        category: 'RELATIVE_MOTION',
        title: 'Peak Closing Velocity',
        observedValue: '8.42 m/s',
        expectedContext: 'Standard delta: 1.5 m/s – 2.8 m/s during braking overlap',
        confidence: 89,
        source: 'Relative Distance 1st Derivative',
        description: 'Significant rate of distance reduction measured between 100m brake point and curb apex.',
        verified: true,
      },
      {
        id: 'ev-3',
        category: 'VEHICLE_RESPONSE',
        title: 'Sudden Lateral Perturbation',
        observedValue: '-0.85 G yaw jerk',
        expectedContext: 'Clean apex trajectory shows steady smooth lateral acceleration curve',
        confidence: 88,
        source: 'Inertial Measurement Unit (IMU CAN-ID 0x24F)',
        description: 'Car 44 experienced an instantaneous yaw acceleration spike coincident with Car 1 apex overlap.',
        verified: true,
      },
      {
        id: 'ev-4',
        category: 'TRAJECTORY',
        title: 'Abnormal Trajectory Delta & Runoff Escape',
        observedValue: '3.8° steering reversal',
        expectedContext: 'Left-hand entry requires continuous positive lock until kerb transition',
        confidence: 84,
        source: 'Steering Angle Sensor + Track Map projection',
        description: 'Car 44 was compelled to abort traditional exit curb radius and take asphalt escape road.',
        verified: true,
      },
      {
        id: 'ev-5',
        category: 'BRAKING',
        title: 'Brake Application Timing & Pressure',
        observedValue: '98.4 bar at 62m',
        expectedContext: 'Standard brake threshold: 100 bar at 110m marker for clean entry',
        confidence: 95,
        source: 'FastF1 Master Cylinder Pressure Sensor',
        description: 'Car 1 executed deep defensive braking with late threshold release.',
        verified: true,
      },
    ],
    relevantRegulations: [
      {
        id: 'reg-33-4',
        document: 'FIA Sporting Regulations 2024',
        article: 'Article 33.4',
        title: 'Manoeuvres during Overtaking and Position Defense',
        regulationTextPlaceholder:
          'At no time may a car be driven unnecessarily slowly, erratically or in a manner which could be deemed potentially dangerous to other drivers or any other person. Manoeuvres liable to hinder other drivers, such as deliberate crowding of a car beyond the edge of the track or any other abnormal change of direction, are strictly prohibited.',
        whyRelevant:
          'The incident involves contested track positioning and spatial allowance during an overtaking manoeuvre into a chicane.',
        matchReason: 'Contested line entry / track margin allowance at chicane apex',
        relevance: 'High',
        source: 'FIA World Motor Sport Council Regulations (Issue 4, 2024)',
      },
      {
        id: 'reg-33-3',
        document: 'FIA Sporting Regulations 2024',
        article: 'Article 33.3',
        title: 'Right to Track Edge and Overlap Thresholds',
        regulationTextPlaceholder:
          'Any driver defending a position on a straight and before any braking area may use the full width of the track during the first move, but must not make more than one change of direction. When approaching a corner, if the overtaking car has significant overlap (front axle alongside front axle or sidepod), reasonable racing room must be preserved.',
        whyRelevant:
          'Evaluates whether the attacking vehicle had established significant geometric overlap prior to turn-in.',
        matchReason: 'Axle-to-axle alignment at braking release phase',
        relevance: 'High',
        source: 'FIA Code of Driving Conduct Guidance Annex',
      },
      {
        id: 'reg-27-3',
        document: 'FIA Sporting Regulations 2024',
        article: 'Article 27.3',
        title: 'Track Limits and Leaving the Circuit',
        regulationTextPlaceholder:
          'Drivers must make every reasonable effort to use the track at all times and may not leave the track without a justifiable reason. If a car leaves the track to avoid an incident, the driver must rejoin safely and without gaining a lasting advantage.',
        whyRelevant:
          'Car 44 rejoined after navigating the Turn 4 escape road speed bumps.',
        matchReason: 'Rejoin safety and lasting advantage evaluation',
        relevance: 'Medium',
        source: 'FIA Sporting Code Chapter IV',
      },
    ],
    evidenceConnections: [
      {
        observedEvidence: 'Minimum gap: 1.82 m & 8.42 m/s closing speed at braking apex',
        relevantRegulation: 'Article 33.4 (Defensive crowding and track edge allowance)',
        stewardReviewAction: 'Examine onboard cameras to confirm if sufficient racing room (1 car width) was maintained on curb.',
      },
      {
        observedEvidence: 'Instantaneous -0.85 G yaw disturbance and steering reversal',
        relevantRegulation: 'Article 33.3 (Significant overlap rights at corner turn-in)',
        stewardReviewAction: 'Verify whether physical wheel contact occurred or if disturbance was aerodynamic wake / curb strike.',
      },
      {
        observedEvidence: 'Car 44 aborting chicane sequence and using secondary escape road',
        relevantRegulation: 'Article 27.3 (Leaving track for avoidance vs gain)',
        stewardReviewAction: 'Verify timing delta upon re-entry to confirm no net lap time gain was acquired.',
      },
    ],
    timeline: [
      {
        timestamp: '13:42:16.8',
        label: 'Approach phase: 150m Board',
        description: 'Both cars at 328 km/h on main approach straight. Distance: 12.4 m.',
        iconType: 'approach',
      },
      {
        timestamp: '13:42:17.8',
        label: 'Cars enter close interaction',
        description: 'Initial threshold braking initiated. Relative lateral spacing begins narrowing.',
        iconType: 'approach',
        evidenceRef: 'Braking Telemetry',
      },
      {
        timestamp: '13:42:18.1',
        label: 'Gap decreases rapidly',
        description: 'Closing speed peaks at 8.42 m/s. Car A commits to defensive inside curb geometry.',
        iconType: 'proximity',
        evidenceRef: 'Closing Velocity Sensor',
      },
      {
        timestamp: '13:42:18.4',
        label: 'Minimum gap detected (1.82 m)',
        description: 'Apex of Turn 4. Critical point of interaction with maximum geometric convergence.',
        iconType: 'contact',
        evidenceRef: 'Optical Radar Gap',
      },
      {
        timestamp: '13:42:18.7',
        label: 'Relative motion increases',
        description: 'Car B exhibits defensive avoidance vector away from apex kerb.',
        iconType: 'motion',
        evidenceRef: 'GPS Trajectory',
      },
      {
        timestamp: '13:42:19.0',
        label: 'Vehicle response detected',
        description: 'Car B registers -0.85 G yaw spike and 3.8° steering angle compensation.',
        iconType: 'response',
        evidenceRef: 'IMU Gyroscope',
      },
      {
        timestamp: '13:42:20.4',
        label: 'Interaction ends & rejoin',
        description: 'Car B navigates escape chicane marker and rejoins track behind Car A.',
        iconType: 'exit',
      },
    ],
    uncertainties: [
      'Visual onboard feed is undergoing sub-millisecond sync calibration with ECU clock.',
      'GPS transponder location may carry ±0.28m measurement noise over high-frequency curb strikes.',
      'Telemetry traces confirm vehicle mechanical behavior but cannot establish driver psychological intent.',
      'This platform produces deterministic evidence reconstruction; it never issues penalties or verdicts.',
      'Final sporting adjudication strictly requires deliberation by appointed FIA Human Race Stewards.',
    ],
  },
  {
    id: 'INC-001',
    session: 'Italian Grand Prix 2024 — Race',
    raceId: 'ita-2024',
    circuit: 'Monza',
    lap: 31,
    turn: 'Turn 4',
    timestamp: '13:42:18',
    timeWindow: { start: '13:42:16.0', end: '13:42:21.0' },
    driverA: 'VER',
    driverB: 'HAM',
    incidentType: 'Possible Contact',
    confidence: 94,
    status: 'REQUIRES_REVIEW',
    severity: 'HIGH',
    summary: 'High-confidence interaction flagged with rapid gap collapse and lateral deceleration anomaly.',
    detectionMethod: 'Telemetry + Optical tracking',
    videoAvailable: true,
    videoPath: '/assets/this-is-formula-one.mp4',
    telemetryAvailable: true,
    regulationsAvailable: true,
    sources: {
      telemetry: 'FastF1 ECU + GPS',
      video: 'World Feed (Linked)',
      regulations: 'FIA Sporting Regulations 2024',
    },
    evidenceAssessment: [],
    relevantRegulations: [],
    evidenceConnections: [],
    timeline: [],
    uncertainties: ['Requires human steward review.'],
  },
  {
    id: 'INC-002',
    session: 'Italian Grand Prix 2024 — Race',
    raceId: 'ita-2024',
    circuit: 'Monza',
    lap: 36,
    turn: 'Turn 1 (Variante del Rettifilo)',
    timestamp: '13:55:21',
    timeWindow: { start: '13:55:18.0', end: '13:55:24.0' },
    driverA: 'NOR',
    driverB: 'PIA',
    incidentType: 'Abnormal Interaction / Late Braking',
    confidence: 78,
    status: 'UNDER_REVIEW',
    severity: 'MEDIUM',
    summary: 'Team intra-rivalry interaction with aggressive cutback line causing lockup on Car 81.',
    detectionMethod: 'Brake pressure gradient delta',
    videoAvailable: false,
    telemetryAvailable: true,
    regulationsAvailable: true,
    sources: {
      telemetry: 'FastF1 ECU',
      video: 'Not yet linked',
      regulations: 'FIA Sporting Code',
    },
    evidenceAssessment: [],
    relevantRegulations: [],
    evidenceConnections: [],
    timeline: [],
    uncertainties: ['Video evidence not yet synchronized.'],
  },
  {
    id: 'INC-003',
    session: 'Italian Grand Prix 2024 — Race',
    raceId: 'ita-2024',
    circuit: 'Monza',
    lap: 42,
    turn: 'Turn 11 (Curva Parabolica / Alboreto)',
    timestamp: '14:03:42',
    timeWindow: { start: '14:03:39.0', end: '14:03:45.0' },
    driverA: 'LEC',
    driverB: 'SAI',
    incidentType: 'Vehicle Disturbance / Slipstream Wake',
    confidence: 88,
    status: 'REVIEWED',
    severity: 'LOW',
    summary: 'High-speed aero wake disturbance detected at entry of Alboreto resulting in slight snap of oversteer.',
    detectionMethod: 'Downforce loss calculation via front pushrod strain gauges',
    videoAvailable: true,
    telemetryAvailable: true,
    regulationsAvailable: true,
    sources: {
      telemetry: 'FastF1 ECU + Strain gauges',
      video: 'World Feed Parabolica',
      regulations: 'FIA Sporting Code',
    },
    evidenceAssessment: [],
    relevantRegulations: [],
    evidenceConnections: [],
    timeline: [],
    uncertainties: ['Concluded as racing aerodynamic circumstance; no infractions noted.'],
  },
  {
    id: 'INC-004',
    session: 'Italian Grand Prix 2024 — Race',
    raceId: 'ita-2024',
    circuit: 'Monza',
    lap: 12,
    turn: 'Turn 1',
    timestamp: '13:18:04',
    timeWindow: { start: '13:18:01.0', end: '13:18:08.0' },
    driverA: 'RUS',
    driverB: 'PER',
    incidentType: 'Wheel-to-Wheel Crowding',
    confidence: 82,
    status: 'REVIEWED',
    severity: 'MEDIUM',
    summary: 'Crowding on outside of Rettifilo chicane. Stewards determined sufficient room provided.',
    detectionMethod: 'Optical track boundaries + GPS',
    videoAvailable: false,
    telemetryAvailable: true,
    regulationsAvailable: true,
    sources: {
      telemetry: 'FastF1 ECU + GPS',
      video: 'Not yet linked',
      regulations: 'FIA Sporting Regulations 2024',
    },
    evidenceAssessment: [],
    relevantRegulations: [],
    evidenceConnections: [],
    timeline: [],
    uncertainties: ['Reviewed by stewards at 13:24.'],
  },
  {
    id: 'INC-005',
    session: 'Italian Grand Prix 2024 — Race',
    raceId: 'ita-2024',
    circuit: 'Monza',
    lap: 1,
    turn: 'Turn 1 & 2',
    timestamp: '13:03:50',
    timeWindow: { start: '13:03:48.0', end: '13:03:54.0' },
    driverA: 'ALO',
    driverB: 'HUL',
    incidentType: 'Close Interaction / Lap 1 Congestion',
    confidence: 74,
    status: 'DETECTED',
    severity: 'LOW',
    summary: 'Opening lap multi-vehicle concertina effect through Rettifilo.',
    detectionMethod: 'Fleet proximity clustering',
    videoAvailable: false,
    telemetryAvailable: true,
    regulationsAvailable: false,
    sources: {
      telemetry: 'GPS Fleet Clustering',
      video: 'Not linked',
      regulations: 'N/A',
    },
    evidenceAssessment: [],
    relevantRegulations: [],
    evidenceConnections: [],
    timeline: [],
    uncertainties: ['Standard Lap 1 race interaction.'],
  },
];

// Generate 50 synchronized high-frequency telemetry points for Lap 31 Turn 4 (13:42:16.0 to 13:42:21.0)
export function generateSynchronizedTelemetry(): TelemetryPoint[] {
  const points: TelemetryPoint[] = [];
  const totalSteps = 50;
  const startSec = 16.0;
  const endSec = 21.0;
  const stepSec = (endSec - startSec) / totalSteps;

  for (let i = 0; i <= totalSteps; i++) {
    const currentSec = startSec + i * stepSec;
    const timeOffset = Number((currentSec - startSec).toFixed(2));
    const timestamp = `13:42:${currentSec.toFixed(1)}`;
    const progress = i / totalSteps; // 0 to 1

    // Braking phase: 0.0 to 0.45
    // Apex phase: 0.45 to 0.55
    // Exit phase: 0.55 to 1.0
    let speedA = 332;
    let throttleA = 100;
    let brakeA = 0;
    let steerA = 0;
    let gearA = 8;
    let accelA = 0.2;

    let speedB = 329;
    let throttleB = 100;
    let brakeB = 0;
    let steerB = 0;
    let gearB = 8;
    let accelB = 0.15;

    let gapMeters = 14.5;
    let closingSpeedMs = 1.2;
    let lateralDistMeters = 4.2;

    if (progress < 0.2) {
      // High speed straight before braking point
      const p = progress / 0.2;
      speedA = Math.round(332 - p * 8);
      speedB = Math.round(329 - p * 6);
      throttleA = 100;
      throttleB = 100;
      brakeA = 0;
      brakeB = 0;
      gearA = 8;
      gearB = 8;
      gapMeters = Number((14.5 - p * 4.0).toFixed(2));
      closingSpeedMs = Number((1.2 + p * 2.5).toFixed(2));
      lateralDistMeters = Number((4.2 - p * 0.4).toFixed(2));
    } else if (progress < 0.48) {
      // Intense threshold braking into Turn 4
      const p = (progress - 0.2) / 0.28;
      speedA = Math.round(324 - p * (324 - 138));
      speedB = Math.round(323 - p * (323 - 144));
      throttleA = Math.max(0, Math.round((1 - p * 2) * 50));
      throttleB = 0;
      brakeA = Math.min(100, Math.round(p * 115));
      brakeB = Math.min(98, Math.round(p * 110));
      gearA = Math.max(3, Math.round(8 - p * 5));
      gearB = Math.max(3, Math.round(8 - p * 5));
      steerA = Number((p * 22).toFixed(1));
      steerB = Number((p * 26).toFixed(1));
      accelA = Number((-4.8 * (1 - Math.abs(p - 0.5))).toFixed(2));
      accelB = Number((-4.6 * (1 - Math.abs(p - 0.5))).toFixed(2));
      gapMeters = Number((10.5 - p * 8.68).toFixed(2)); // falls toward 1.82m
      closingSpeedMs = Number((3.7 + p * 4.72).toFixed(2)); // peaks at 8.42 m/s
      lateralDistMeters = Number((3.8 - p * 1.98).toFixed(2)); // down to 1.82m
    } else if (progress < 0.58) {
      // APEX & INCIDENT WINDOW: minimum gap 1.82m, steering reversal, sudden yaw
      const p = (progress - 0.48) / 0.10;
      speedA = Math.round(138 + p * 8);
      speedB = Math.round(144 - p * 14); // Car B perturbed
      throttleA = Math.round(15 + p * 25);
      throttleB = Math.round(Math.max(0, 10 - p * 10)); // throttle lift on car B
      brakeA = Math.round(15 * (1 - p));
      brakeB = Math.round(45 * p); // emergency stab
      gearA = 3;
      gearB = 3;
      steerA = Number((22 + p * 3).toFixed(1));
      // Car B steering anomaly: sharp counter-steering correction -3.8°
      steerB = Number((26 - p * 29.8).toFixed(1));
      accelA = Number((1.8 * p).toFixed(2));
      accelB = Number((-0.85).toFixed(2)); // perturbation
      gapMeters = Number((1.82 + p * 1.1).toFixed(2));
      closingSpeedMs = Number((8.42 - p * 4.8).toFixed(2));
      lateralDistMeters = Number((1.82 + p * 1.6).toFixed(2));
    } else {
      // Exit & acceleration into Curva Grande / Roggia exit
      const p = (progress - 0.58) / 0.42;
      speedA = Math.round(146 + p * (248 - 146));
      speedB = Math.round(130 + p * (220 - 130));
      throttleA = Math.min(100, Math.round(40 + p * 60));
      throttleB = Math.min(100, Math.round(20 + p * 75));
      brakeA = 0;
      brakeB = 0;
      gearA = Math.min(6, Math.round(3 + p * 3));
      gearB = Math.min(5, Math.round(3 + p * 2));
      steerA = Number((25 * (1 - p)).toFixed(1));
      steerB = Number((5 * (1 - p)).toFixed(1));
      accelA = Number((2.4 * p).toFixed(2));
      accelB = Number((1.9 * p).toFixed(2));
      gapMeters = Number((2.92 + p * 9.5).toFixed(2));
      closingSpeedMs = Number((3.62 - p * 4.2).toFixed(2));
      lateralDistMeters = Number((3.42 + p * 2.8).toFixed(2));
    }

    points.push({
      timeOffset,
      timestamp,
      speedA,
      throttleA,
      brakeA,
      steerA,
      gearA,
      accelA,
      speedB,
      throttleB,
      brakeB,
      steerB,
      gearB,
      accelB,
      gapMeters: Math.max(1.82, gapMeters),
      closingSpeedMs,
      lateralDistMeters,
    });
  }

  return points;
}

export const MOCK_REGULATION_LIBRARY: RelevantRegulation[] = [
  {
    id: 'reg-33-4',
    document: 'FIA Sporting Regulations 2024',
    article: 'Article 33.4',
    title: 'Manoeuvres during Overtaking and Position Defense',
    regulationTextPlaceholder:
      'At no time may a car be driven unnecessarily slowly, erratically or in a manner which could be deemed potentially dangerous to other drivers or any other person. Manoeuvres liable to hinder other drivers, such as deliberate crowding of a car beyond the edge of the track or any other abnormal change of direction, are strictly prohibited.',
    whyRelevant: 'Investigates track positioning and spatial allowance during an overtaking manoeuvre.',
    matchReason: 'Contested line entry / track margin allowance at chicane apex',
    relevance: 'High',
    source: 'FIA World Motor Sport Council Regulations (Issue 4, 2024)',
  },
  {
    id: 'reg-33-3',
    document: 'FIA Sporting Regulations 2024',
    article: 'Article 33.3',
    title: 'Right to Track Edge and Overlap Thresholds',
    regulationTextPlaceholder:
      'Any driver defending a position on a straight and before any braking area may use the full width of the track during the first move, but must not make more than one change of direction. More than one change of direction to defend a position is not permitted.',
    whyRelevant: 'Evaluates if defending car performed illegal secondary directional shift under braking.',
    matchReason: 'Braking vector trajectory delta',
    relevance: 'High',
    source: 'FIA Code of Driving Conduct Guidance Annex',
  },
  {
    id: 'reg-27-3',
    document: 'FIA Sporting Regulations 2024',
    article: 'Article 27.3',
    title: 'Track Limits and Leaving the Circuit',
    regulationTextPlaceholder:
      'Drivers must make every reasonable effort to use the track at all times and may not leave the track without a justifiable reason. If a car leaves the track to avoid an incident, the driver must rejoin safely and without gaining a lasting advantage.',
    whyRelevant: 'Relevant when vehicle is forced to use secondary escape tarmac road at chicane.',
    matchReason: 'Rejoin safety and lasting advantage evaluation',
    relevance: 'Medium',
    source: 'FIA Sporting Code Chapter IV',
  },
  {
    id: 'reg-app-l-iv',
    document: 'FIA International Sporting Code Appendix L',
    article: 'Chapter IV, Article 2',
    title: 'Overtaking, Car Control and Track Limits',
    regulationTextPlaceholder:
      'A car being overtaken must give room if the overtaking car has its front axle at least alongside the rear axle of the defending car before the braking point. At the apex, both drivers must leave a minimum of one full car width to the white boundary line.',
    whyRelevant: 'Defines geometric parameters required for legitimate claims to apex real estate.',
    matchReason: 'Front-to-rear axle alignment calculation',
    relevance: 'High',
    source: 'FIA ISC Appendix L 2024',
  },
  {
    id: 'reg-app-h',
    document: 'FIA Sporting Code Appendix H',
    article: 'Article 2.5.5',
    title: 'Flags, Signals and Safety Car Protocols',
    regulationTextPlaceholder:
      'Rules regarding yellow flag compliance, speed reductions, and overtaking prohibitions under hazard conditions.',
    whyRelevant: 'Verifies whether local yellow flags were displayed in sector at time of interaction.',
    matchReason: 'Sector flag status audit',
    relevance: 'Low',
    source: 'FIA ISC Appendix H 2024',
  },
];

export const MOCK_ASSISTANT_CONVERSATION: AssistantMessage[] = [
  {
    id: 'msg-1',
    sender: 'assistant',
    timestamp: '13:43:02',
    text: 'Motorsport Incident Intelligence assistant initialized. I am synchronized with session telemetry, optical evidence, and FIA 2024 regulatory references for Incident #024 (Lap 31, Turn 4). How may I assist your evidence assessment?',
    suggestedFollowUps: [
      'Why was this incident flagged?',
      'What changed in the telemetry?',
      'Which regulations may be relevant?',
      'What evidence supports this assessment?',
      'What evidence is missing?',
    ],
  },
];

export const MOCK_ASSISTANT_MESSAGES = MOCK_ASSISTANT_CONVERSATION;

export const MOCK_RACE_ACTIVITY = [
  { lap: 1, candidates: 42, abnormal: 14, highConfidence: 2 },
  { lap: 5, candidates: 21, abnormal: 6, highConfidence: 0 },
  { lap: 10, candidates: 18, abnormal: 4, highConfidence: 0 },
  { lap: 12, candidates: 29, abnormal: 9, highConfidence: 1 },
  { lap: 18, candidates: 24, abnormal: 5, highConfidence: 0 },
  { lap: 24, candidates: 19, abnormal: 7, highConfidence: 0 },
  { lap: 31, candidates: 58, abnormal: 26, highConfidence: 4 }, // Incident #024
  { lap: 36, candidates: 41, abnormal: 18, highConfidence: 2 },
  { lap: 42, candidates: 33, abnormal: 12, highConfidence: 1 },
  { lap: 48, candidates: 15, abnormal: 3, highConfidence: 0 },
  { lap: 53, candidates: 12, abnormal: 2, highConfidence: 0 },
];
