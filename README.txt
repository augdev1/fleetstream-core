===================================================================
 FLEETSTREAM - LOCAL VIDEO ORCHESTRATOR FOR IPHONE FLEETS
===================================================================

This package contains everything needed to automate video distribution
and metadata generation for your 4 iPhones on Tame.so.

-------------------------------------------------------------------
 QUICK 3-STEP SETUP
-------------------------------------------------------------------

1. RUN THE INSTALLER (ONE TIME ONLY):
   - Windows: Double-click "INSTALL.bat".
   - macOS: Double-click "INSTALL.command".
   This will automatically configure the isolated Python environment
   and install all required dependencies.
   Wait until it displays "[SUCCESS] FleetStream environment ready!".

2. START THE SERVICE:
   - Windows: Double-click "START_FLEETSTREAM.bat".
   - macOS: Double-click "START_FLEETSTREAM.command".
   Keep the window open or minimized in the background.
   The orchestrator is now actively monitoring for incoming videos.

3. DROP VIDEOS:
   Whenever you have reels/videos to post, simply drag and drop them
   into the "inbox" folder.
   
   FleetStream will automatically:
   - Detect and safely stabilize file copies.
   - Deliver videos across your 4 iPhones (devices/iphone_01 to iphone_04).
   - Generate matching .json metadata files with viral captions and hashtags.
   - Clean the inbox folder so it remains ready for the next batch.

-------------------------------------------------------------------
 CUSTOM CONFIGURATION (config.json)
-------------------------------------------------------------------

You can open "config.json" with Notepad to adjust:
- "mode": "broadcast" (Default: mirrors every video to all 4 iPhones)
          "round_robin" (Divides videos evenly among the 4 iPhones)
- "default_hashtags": Set your custom niche/brand hashtags.
- "default_captions": Set your preferred viral caption hooks.
- "inbox_dir": Custom folder where you drop incoming videos.
- "devices_dir": Custom target directory for your Tame.so phone folders.
  (Remember to use forward slashes in paths, e.g. "C:/Videos/Inbox")

-------------------------------------------------------------------
 SUPPORT & ASSISTANCE
-------------------------------------------------------------------
If you need any adjustments or questions, reach out directly.
