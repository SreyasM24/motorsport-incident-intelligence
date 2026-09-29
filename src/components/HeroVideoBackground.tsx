import React, { useRef, useEffect, useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

export const HeroVideoBackground: React.FC = () => {
  const videoRefA = useRef<HTMLVideoElement | null>(null);
  const videoRefB = useRef<HTMLVideoElement | null>(null);
  const [activePlayer, setActivePlayer] = useState<'A' | 'B'>('A');
  const [readyA, setReadyA] = useState(false);
  const [readyB, setReadyB] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  // Video source paths (both formatted name and URL-encoded uploaded name)
  const PRIMARY_VIDEO_SRC = '/this-is-formula-one.mp4';
  const ALT_VIDEO_SRC = encodeURI('/This is Formula One - noway- (1080p, h264) (1) (1).mp4');

  // Hard requirement: Always skip the first 5 seconds. Range is strictly 00:05 -> END.
  const START_OFFSET_SECONDS = 5.0;
  const CROSSFADE_WINDOW_SECONDS = 0.9;
  const CROSSFADE_DURATION_MS = 750;

  const activePlayerRef = useRef<'A' | 'B'>('A');
  const isTransitioningRef = useRef(false);
  const isMutedRef = useRef(true);

  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  useEffect(() => {
    const videoA = videoRefA.current;
    const videoB = videoRefB.current;
    if (!videoA) return;

    // Helper to strictly clamp any time under 5.0 seconds
    const enforceMinOffset = (video: HTMLVideoElement) => {
      if (video.currentTime < START_OFFSET_SECONDS) {
        video.currentTime = START_OFFSET_SECONDS;
      }
    };

    // Transition between dual players for seamless, non-stop loop
    const triggerTransitionTo = (target: 'A' | 'B') => {
      if (isTransitioningRef.current) return;
      isTransitioningRef.current = true;

      const incoming = target === 'A' ? videoA : videoB;
      const outgoing = target === 'A' ? videoB : videoA;

      if (incoming) {
        incoming.currentTime = START_OFFSET_SECONDS;
        incoming.muted = isMutedRef.current;
        const playPromise = incoming.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              if (target === 'A') setReadyA(true);
              else setReadyB(true);
              activePlayerRef.current = target;
              setActivePlayer(target);
            })
            .catch(() => {
              activePlayerRef.current = target;
              setActivePlayer(target);
            });
        } else {
          activePlayerRef.current = target;
          setActivePlayer(target);
        }
      }

      // After crossfade finishes, pause and reset the hidden outgoing player to 00:05
      setTimeout(() => {
        if (outgoing) {
          outgoing.pause();
          outgoing.currentTime = START_OFFSET_SECONDS;
          outgoing.muted = true;
        }
        isTransitioningRef.current = false;
      }, CROSSFADE_DURATION_MS);
    };

    // --- Configure Video A ---
    videoA.muted = true;
    videoA.playsInline = true;
    videoA.currentTime = START_OFFSET_SECONDS;

    const handleLoadedMetadataA = () => {
      videoA.currentTime = START_OFFSET_SECONDS;
    };

    const handleCanPlayA = () => {
      enforceMinOffset(videoA);
    };

    const handleSeekedA = () => {
      if (videoA.currentTime >= START_OFFSET_SECONDS) {
        setReadyA(true);
      }
    };

    const handleTimeUpdateA = () => {
      enforceMinOffset(videoA);
      if (videoA.currentTime >= START_OFFSET_SECONDS) {
        setReadyA(true);
      }

      // Check if approaching loop point
      if (
        videoA.duration &&
        videoA.duration > START_OFFSET_SECONDS &&
        !isTransitioningRef.current &&
        activePlayerRef.current === 'A'
      ) {
        const timeLeft = videoA.duration - videoA.currentTime;
        if (timeLeft <= CROSSFADE_WINDOW_SECONDS) {
          triggerTransitionTo('B');
        }
      }
    };

    const handleEndedA = () => {
      // Requirement 5: Listen for ended event and manually enforce currentTime = 5; video.play()
      videoA.currentTime = START_OFFSET_SECONDS;
      if (activePlayerRef.current === 'A') {
        triggerTransitionTo('B');
      }
    };

    videoA.addEventListener('loadedmetadata', handleLoadedMetadataA);
    videoA.addEventListener('canplay', handleCanPlayA);
    videoA.addEventListener('seeked', handleSeekedA);
    videoA.addEventListener('timeupdate', handleTimeUpdateA);
    videoA.addEventListener('ended', handleEndedA);

    // Initial startup on Video A
    const startInitialPlay = () => {
      videoA.currentTime = START_OFFSET_SECONDS;
      const p = videoA.play();
      if (p !== undefined) {
        p.then(() => {
          if (videoA.currentTime >= START_OFFSET_SECONDS) {
            setReadyA(true);
          }
        }).catch(() => {
          // Autoplay rejection handled gracefully
        });
      }
    };
    startInitialPlay();

    // Fallback on first user interaction if browser policy delayed autoplay
    const handleFirstInteraction = () => {
      if (videoA && videoA.paused) {
        enforceMinOffset(videoA);
        videoA.play().then(() => setReadyA(true)).catch(() => {});
      }
    };
    window.addEventListener('pointerdown', handleFirstInteraction, { once: true });
    window.addEventListener('keydown', handleFirstInteraction, { once: true });

    // --- Configure Video B (Standby player for seamless crossfade) ---
    let handleLoadedMetadataB: () => void;
    let handleCanPlayB: () => void;
    let handleSeekedB: () => void;
    let handleTimeUpdateB: () => void;
    let handleEndedB: () => void;

    if (videoB) {
      videoB.muted = true;
      videoB.playsInline = true;
      videoB.currentTime = START_OFFSET_SECONDS;

      handleLoadedMetadataB = () => {
        videoB.currentTime = START_OFFSET_SECONDS;
      };

      handleCanPlayB = () => {
        enforceMinOffset(videoB);
      };

      handleSeekedB = () => {
        if (videoB.currentTime >= START_OFFSET_SECONDS) {
          setReadyB(true);
        }
      };

      handleTimeUpdateB = () => {
        enforceMinOffset(videoB);
        if (videoB.currentTime >= START_OFFSET_SECONDS) {
          setReadyB(true);
        }

        // Check if approaching loop point
        if (
          videoB.duration &&
          videoB.duration > START_OFFSET_SECONDS &&
          !isTransitioningRef.current &&
          activePlayerRef.current === 'B'
        ) {
          const timeLeft = videoB.duration - videoB.currentTime;
          if (timeLeft <= CROSSFADE_WINDOW_SECONDS) {
            triggerTransitionTo('A');
          }
        }
      };

      handleEndedB = () => {
        // Requirement 5: Listen for ended event and manually enforce currentTime = 5; video.play()
        videoB.currentTime = START_OFFSET_SECONDS;
        if (activePlayerRef.current === 'B') {
          triggerTransitionTo('A');
        }
      };

      videoB.addEventListener('loadedmetadata', handleLoadedMetadataB);
      videoB.addEventListener('canplay', handleCanPlayB);
      videoB.addEventListener('seeked', handleSeekedB);
      videoB.addEventListener('timeupdate', handleTimeUpdateB);
      videoB.addEventListener('ended', handleEndedB);
      videoB.load();
    }

    return () => {
      window.removeEventListener('pointerdown', handleFirstInteraction);
      window.removeEventListener('keydown', handleFirstInteraction);

      videoA.removeEventListener('loadedmetadata', handleLoadedMetadataA);
      videoA.removeEventListener('canplay', handleCanPlayA);
      videoA.removeEventListener('seeked', handleSeekedA);
      videoA.removeEventListener('timeupdate', handleTimeUpdateA);
      videoA.removeEventListener('ended', handleEndedA);

      if (videoB) {
        videoB.removeEventListener('loadedmetadata', handleLoadedMetadataB);
        videoB.removeEventListener('canplay', handleCanPlayB);
        videoB.removeEventListener('seeked', handleSeekedB);
        videoB.removeEventListener('timeupdate', handleTimeUpdateB);
        videoB.removeEventListener('ended', handleEndedB);
      }
    };
  }, []); // Run once on mount to establish persistent, continuous loop

  const toggleMute = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    isMutedRef.current = newMuted;

    const currentActive = activePlayerRef.current === 'A' ? videoRefA.current : videoRefB.current;
    const inactive = activePlayerRef.current === 'A' ? videoRefB.current : videoRefA.current;

    if (currentActive) {
      currentActive.muted = newMuted;
    }
    if (inactive) {
      inactive.muted = true;
    }
  };

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none select-none z-0 bg-[#07090c]">
      {/* Video Instance A (Independent enforcement of 00:05 start) */}
      <video
        ref={videoRefA}
        autoPlay
        muted={isMuted}
        playsInline
        preload="auto"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ease-in-out ${
          activePlayer === 'A' && readyA ? 'opacity-80' : 'opacity-0'
        }`}
        style={{
          transform: 'scale(1.12)',
          transformOrigin: 'center center',
          objectPosition: 'center 40%',
        }}
      >
        <source src={PRIMARY_VIDEO_SRC} type="video/mp4" />
        <source src={ALT_VIDEO_SRC} type="video/mp4" />
      </video>

      {/* Video Instance B (Independent enforcement of 00:05 start for seamless loop crossfade) */}
      <video
        ref={videoRefB}
        autoPlay
        muted={isMuted}
        playsInline
        preload="auto"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ease-in-out ${
          activePlayer === 'B' && readyB ? 'opacity-80' : 'opacity-0'
        }`}
        style={{
          transform: 'scale(1.12)',
          transformOrigin: 'center center',
          objectPosition: 'center 40%',
        }}
      >
        <source src={PRIMARY_VIDEO_SRC} type="video/mp4" />
        <source src={ALT_VIDEO_SRC} type="video/mp4" />
      </video>

      {/* Multi-tier Cinematic Dark Gradient Overlays for optimal readability without losing track action */}
      {/* 1. Deep radial vignette */}
      <div 
        className="absolute inset-0 z-10 pointer-events-none" 
        style={{
          background: 'radial-gradient(ellipse at center, rgba(10,10,11,0.2) 0%, rgba(10,10,11,0.65) 60%, rgba(10,10,11,0.92) 100%)'
        }}
      />

      {/* 2. Vertical top & bottom editorial gradients */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0b]/80 via-transparent to-[#0a0a0b] z-10 pointer-events-none" />
      
      {/* 3. Subtle telemetry scanline overlay for motorsport tech feel */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(18,24,38,0)_50%,rgba(0,0,0,0.3)_50%)] bg-[length:100%_4px] opacity-35 z-10 pointer-events-none" />

      {/* Audio Toggle Control */}
      <div className="absolute bottom-6 right-8 z-30 pointer-events-auto">
        <button
          onClick={toggleMute}
          className="flex items-center gap-2 px-3 py-1.5 rounded-sm bg-black/70 hover:bg-black/90 border border-white/15 text-white/70 hover:text-white transition-all text-[11px] font-mono backdrop-blur-md cursor-pointer"
          title={isMuted ? 'Unmute video audio' : 'Mute video audio'}
        >
          {isMuted ? (
            <>
              <VolumeX className="w-3.5 h-3.5 text-red-500" />
              <span className="uppercase tracking-wider">AUDIO OFF</span>
            </>
          ) : (
            <>
              <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="uppercase tracking-wider text-emerald-400">AUDIO ON</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
