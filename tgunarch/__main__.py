# -*- coding: utf-8 -*-

# Standard library imports
import asyncio  # For asynchronous operations
import os  # For interacting with the operating system (creating dirs, checking files)
import signal  # For handling system signals (like CTRL+C)
import time  # For getting current time

# Third-party imports
from pyrogram import idle  # Pyrogram function to keep the client running idly

# Local application/library specific imports
from config import Config  # Importing configuration variables

# Importing components from the current package (.)
from . import LOGGER, unzipbot_client  # Importing logger instance and the Pyrogram client instance
from .others.db.database import get_lang  # Function to get language strings from the database
from .others.start import (  # Importing startup helper functions
    check_logs,  # Function to check log channel validity
    dl_thumbs,  # Function to download thumbnails
    remove_expired_tasks,  # Function to remove old tasks from the database
    set_boot_time,  # Function to record the bot's boot time
    start_cron_jobs,  # Function to start scheduled background tasks
)
from .bucket.messages import Messages  # Class to handle fetching localized messages


# Initialize the Messages class with the language fetcher function
# This allows fetching text strings based on context and language preference
LOGGER.info("Initializing Messages class for localization.")
try:
    messages = Messages(lang_fetcher=get_lang)
    LOGGER.info("Messages class initialized successfully.")
except Exception as e:
    # Log critical error if message system fails to initialize
    LOGGER.critical(f"FATAL: Failed to initialize Messages class: {e}", exc_info=True)
    # We might want to exit here if messages are critical, but we'll let it proceed for now.
    messages = None # Set to None to handle potential failures later if possible

# --- Graceful Shutdown Function ---
async def async_shutdown_bot():
    """
    Handles the asynchronous shutdown process for the bot.
    Cancels ongoing tasks, sends final messages/logs, and stops the client.
    """
    LOGGER.info("Starting asynchronous shutdown process...")
    # Record the time of shutdown
    stoptime = time.strftime("%Y/%m/%d - %H:%M:%S")
    LOGGER.info(f"Bot shutdown initiated at: {stoptime}")

    # Retrieve the shutdown message string
    shutdown_message_text = "Bot is stopping." # Default message
    if messages:
        try:
            shutdown_message_text = messages.get("main", "STOP_TXT", None, stoptime)
            LOGGER.info("Retrieved localized shutdown message.")
        except Exception as e:
            LOGGER.error(f"Error getting shutdown message string: {e}", exc_info=True)
    else:
        LOGGER.warning("Messages object not available, using default shutdown message.")

    LOGGER.info(shutdown_message_text) # Log the shutdown message locally

    # Cancel all running asyncio tasks except the current one (this shutdown task)
    LOGGER.info("Identifying tasks to cancel...")
    try:
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        LOGGER.info(f"Found {len(tasks)} tasks to cancel.")
        if tasks:
            LOGGER.info("Cancelling tasks...")
            # Request cancellation for each task
            [task.cancel() for task in tasks]
            # Wait for tasks to finish cancellation
            LOGGER.info("Waiting for tasks to complete cancellation...")
            await asyncio.gather(*tasks, return_exceptions=True)
            LOGGER.info("Tasks cancelled.")
        else:
            LOGGER.info("No tasks needed cancellation.")
    except Exception as e:
        LOGGER.error(f"Error during task cancellation: {e}", exc_info=True)

    # Try to send a final message and the log file to the LOGS_CHANNEL
    LOGGER.info(f"Attempting to send shutdown notification to LOGS_CHANNEL: {Config.LOGS_CHANNEL}")
    try:
        # Ensure client is still connected before sending
        if unzipbot_client.is_connected:
            await unzipbot_client.send_message(
                chat_id=Config.LOGS_CHANNEL,
                text=shutdown_message_text,
            )
            LOGGER.info("Shutdown message sent to LOGS_CHANNEL.")
        else:
            LOGGER.warning("Client not connected, cannot send shutdown message.")

        # Try to send the log file
        log_file_path = "unzip-bot.log"
        LOGGER.info(f"Attempting to send log file '{log_file_path}' to LOGS_CHANNEL.")
        if os.path.exists(log_file_path):
            try:
                 # Ensure client is still connected before sending
                if unzipbot_client.is_connected:
                    with open(log_file_path, "rb") as doc_f:
                        await unzipbot_client.send_document(
                            chat_id=Config.LOGS_CHANNEL,
                            document=doc_f,
                            file_name=doc_f.name,
                        )
                    LOGGER.info(f"Log file '{log_file_path}' sent to LOGS_CHANNEL.")
                else:
                     LOGGER.warning("Client not connected, cannot send log file.")
            except FileNotFoundError:
                 LOGGER.warning(f"Log file '{log_file_path}' not found, cannot send.")
            except Exception as e:
                # Log error if sending the document fails (e.g., file too large, permissions)
                LOGGER.error(f"Failed to send log file to LOGS_CHANNEL: {e}", exc_info=True)
        else:
            LOGGER.info(f"Log file '{log_file_path}' does not exist, skipping sending.")

    except Exception as e:
        # Log error if sending the initial message fails (e.g., permissions, channel not found)
        error_message_text = f"Error during shutdown message sending: {e}"
        if messages:
            try:
                error_message_text = messages.get("main", "ERROR_SHUTDOWN_MSG", None, e)
            except Exception as msg_e:
                 LOGGER.error(f"Error getting shutdown error message string: {msg_e}", exc_info=True)

        LOGGER.error(error_message_text, exc_info=True)

    # Perform final cleanup
    finally:
        LOGGER.info("Stopping the Pyrogram client...")
        try:
            await unzipbot_client.stop() # Stop the Pyrogram client session
            LOGGER.info("Pyrogram client stopped successfully.")
            # Log the final bot stopped message
            final_stop_message = "Bot stopped."
            if messages:
                try:
                    final_stop_message = messages.get("main", "BOT_STOPPED")
                except Exception as e:
                    LOGGER.error(f"Error getting final bot stopped message string: {e}", exc_info=True)
            LOGGER.info(final_stop_message)
        except Exception as e:
            LOGGER.error(f"Error while stopping the Pyrogram client: {e}", exc_info=True)

    LOGGER.info("Asynchronous shutdown process completed.")


# --- Signal Handling Function ---
def handle_stop_signals(signum, frame):
    """
    Callback function to handle termination signals (SIGINT, SIGTERM).
    Initiates the asynchronous shutdown process.

    Args:
        signum (int): The signal number received.
        frame: The current stack frame (unused here, but required by signal handler signature).
    """
    signal_name = signal.Signals(signum).name
    LOGGER.info(f"Received stop signal: {signal_name} (Signum: {signum}). Frame: {frame}")
    # Retrieve the signal received message string
    signal_message_text = f"Received stop signal {signal_name}"
    if messages:
        try:
            signal_message_text = messages.get(
                "main",
                "RECEIVED_STOP_SIGNAL",
                None,
                signal_name,
                signum,
                frame, # Note: frame object might not be easily serializable or useful in a message string
            )
            LOGGER.info("Retrieved localized signal received message.")
        except Exception as e:
            LOGGER.error(f"Error getting signal received message string: {e}", exc_info=True)

    LOGGER.info(signal_message_text) # Log the message locally

    # Get the current asyncio event loop
    LOGGER.info("Getting asyncio event loop to schedule shutdown task.")
    try:
        loop = asyncio.get_event_loop()
        # Check if the loop is running before creating a task
        if loop.is_running():
            LOGGER.info("Event loop is running. Creating shutdown task.")
            # Create a task to run the async shutdown function
            loop.create_task(async_shutdown_bot())
            LOGGER.info("Shutdown task created successfully.")
        else:
            LOGGER.warning("Event loop is not running. Cannot schedule async shutdown.")
            # Fallback: Try running shutdown synchronously if loop isn't running (might block)
            # Although ideally signals are caught while loop is running.
            # asyncio.run(async_shutdown_bot()) # This might not be safe depending on context
    except RuntimeError as e:
        LOGGER.error(f"Error getting event loop or creating shutdown task: {e}", exc_info=True)
    except Exception as e:
         LOGGER.error(f"Unexpected error in handle_stop_signals: {e}", exc_info=True)

    LOGGER.info(f"Stop signal {signal_name} handling initiated.")


# --- Signal Handler Setup Function ---
def setup_signal_handlers():
    """
    Sets up signal handlers for SIGINT (CTRL+C) and SIGTERM.
    """
    LOGGER.info("Setting up signal handlers...")
    try:
        # Get the current asyncio event loop
        loop = asyncio.get_event_loop()
        LOGGER.info("Retrieved event loop for signal handlers.")

        # Define the signals to handle
        signals_to_handle = (signal.SIGINT, signal.SIGTERM)

        # Register the handler for each specified signal
        for sig in signals_to_handle:
            signal_name = signal.Signals(sig).name
            LOGGER.info(f"Adding handler for signal: {signal_name} ({sig})")
            # loop.add_signal_handler expects the handler function first, then args
            # Use lambda to pass the specific signal number 's' to the handler
            loop.add_signal_handler(sig, lambda s=sig: handle_stop_signals(s, None))
            LOGGER.info(f"Handler added successfully for {signal_name}.")

        LOGGER.info("Signal handlers set up successfully.")
    except Exception as e:
        LOGGER.error(f"Failed to set up signal handlers: {e}", exc_info=True)
        # Depending on the severity, might want to raise this error or exit


# --- Main Bot Execution Function ---
async def main():
    """
    The main asynchronous function that sets up and runs the bot.
    """
    LOGGER.info("Starting main bot execution function...")
    lock_file_removed_on_error = False # Flag to track if lock file was handled in exception

    try:
        # --- Directory Setup ---
        LOGGER.info(f"Ensuring download directory exists: {Config.DOWNLOAD_LOCATION}")
        try:
            os.makedirs(Config.DOWNLOAD_LOCATION, exist_ok=True) # Create download directory if it doesn't exist
            LOGGER.info(f"Download directory ensured: {Config.DOWNLOAD_LOCATION}")
        except OSError as e:
            LOGGER.error(f"Error creating download directory {Config.DOWNLOAD_LOCATION}: {e}", exc_info=True)
            # Potentially exit or raise if this directory is critical
            raise  # Re-raise the error to stop execution if directory creation fails

        LOGGER.info(f"Ensuring thumbnail directory exists: {Config.THUMB_LOCATION}")
        try:
            os.makedirs(Config.THUMB_LOCATION, exist_ok=True) # Create thumbnail directory if it doesn't exist
            LOGGER.info(f"Thumbnail directory ensured: {Config.THUMB_LOCATION}")
        except OSError as e:
            LOGGER.error(f"Error creating thumbnail directory {Config.THUMB_LOCATION}: {e}", exc_info=True)
            # Decide if this is critical - perhaps log warning and continue if thumbs aren't essential
            LOGGER.warning("Proceeding without guaranteed thumbnail directory.")

        # --- Lock File Handling ---
        # This prevents running multiple instances simultaneously
        LOGGER.info(f"Checking for existing lock file: {Config.LOCKFILE}")
        try:
            if os.path.exists(Config.LOCKFILE):
                LOGGER.warning(f"Lock file {Config.LOCKFILE} found. Assuming previous instance crashed or didn't clean up. Removing it.")
                try:
                    os.remove(Config.LOCKFILE)
                    LOGGER.info("Existing lock file removed.")
                except OSError as e:
                    LOGGER.error(f"Error removing existing lock file {Config.LOCKFILE}: {e}. Please check permissions.", exc_info=True)
                    raise # Cannot proceed if lock file cannot be managed

            # Create a new lock file
            LOGGER.info(f"Creating lock file: {Config.LOCKFILE}")
            with open(Config.LOCKFILE, "w") as lock_f:
                lock_f.write(str(os.getpid())) # Write process ID for potential debugging
            LOGGER.info(f"Lock file {Config.LOCKFILE} created.")
        except IOError as e:
             LOGGER.error(f"Error handling lock file {Config.LOCKFILE}: {e}", exc_info=True)
             raise # Cannot proceed without lock file

        # --- Start Pyrogram Client ---
        LOGGER.info("Starting the Pyrogram client...")
        if messages:
             start_message_key = messages.get("main", "STARTING_BOT")
             LOGGER.info(start_message_key if start_message_key else "Attempting to start bot client...")
        try:
            await unzipbot_client.start()
            LOGGER.info("Pyrogram client started successfully.")
        except Exception as e:
            LOGGER.error(f"FATAL: Failed to start Pyrogram client: {e}", exc_info=True)
            raise # Critical error, cannot continue

        # --- Send Startup Notification ---
        starttime = time.strftime("%Y/%m/%d - %H:%M:%S")
        LOGGER.info(f"Bot started at: {starttime}")
        LOGGER.info(f"Attempting to send startup message to LOGS_CHANNEL: {Config.LOGS_CHANNEL}")
        start_message_text = f"Bot started at {starttime}" # Default message
        if messages:
            try:
                start_message_text = messages.get("main", "START_TXT", None, starttime)
                LOGGER.info("Retrieved localized startup message.")
            except Exception as e:
                LOGGER.error(f"Error getting startup message string: {e}", exc_info=True)
        else:
            LOGGER.warning("Messages object not available, using default startup message.")

        try:
            await unzipbot_client.send_message(
                chat_id=Config.LOGS_CHANNEL,
                text=start_message_text,
            )
            LOGGER.info("Startup message sent to LOGS_CHANNEL.")
        except Exception as e:
            # Log error if sending fails (e.g., bot not in channel, permissions)
            LOGGER.error(f"Failed to send startup message to LOGS_CHANNEL {Config.LOGS_CHANNEL}: {e}", exc_info=True)
            # Continue execution even if message fails, but log it prominently.

        # --- Set Boot Time ---
        LOGGER.info("Setting bot boot time...")
        try:
            await set_boot_time()
            LOGGER.info("Bot boot time set successfully.")
        except Exception as e:
            LOGGER.error(f"Error setting bot boot time: {e}", exc_info=True)
            # Log and continue, boot time might not be critical

        # --- Check Logs Channel ---
        LOGGER.info("Checking log channel configuration...")
        log_check_message = "Checking logs..." # Default
        if messages:
            try:
                log_check_message = messages.get("main", "CHECK_LOG")
            except Exception as e:
                 LOGGER.error(f"Error getting log check message string: {e}", exc_info=True)
        LOGGER.info(log_check_message)

        log_check_passed = False
        try:
            log_check_passed = await check_logs()
        except Exception as e:
             LOGGER.error(f"Error occurred during log check: {e}", exc_info=True)
             # Treat error during check as failure

        # --- Main Execution Path or Shutdown based on Log Check ---
        if log_check_passed:
            LOGGER.info("Log channel check successful.")
            log_checked_message = "Log channel checked." # Default
            if messages:
                try:
                    log_checked_message = messages.get("main", "LOG_CHECKED")
                except Exception as e:
                     LOGGER.error(f"Error getting log checked message string: {e}", exc_info=True)
            LOGGER.info(log_checked_message)

            # --- Setup Signal Handlers ---
            LOGGER.info("Proceeding with bot setup: Setting up signal handlers.")
            try:
                setup_signal_handlers() # Setup handlers for graceful shutdown
            except Exception as e:
                 # Error already logged in setup_signal_handlers
                 LOGGER.warning("Continuing execution despite potential issue setting up signal handlers.")

            # --- Run Startup Tasks ---
            LOGGER.info("Running initial tasks: removing expired tasks, downloading thumbs, starting cron jobs.")
            try:
                LOGGER.info("Removing expired tasks...")
                await remove_expired_tasks(True) # Remove tasks older than configured expiry
                LOGGER.info("Expired tasks removed.")
            except Exception as e:
                LOGGER.error(f"Error during expired task removal: {e}", exc_info=True)
                # Log and continue

            try:
                LOGGER.info("Downloading/checking thumbnails...")
                await dl_thumbs() # Download necessary thumbnails
                LOGGER.info("Thumbnail download/check completed.")
            except Exception as e:
                LOGGER.error(f"Error during thumbnail download: {e}", exc_info=True)
                # Log and continue if thumbnails aren't critical

            try:
                LOGGER.info("Starting cron jobs...")
                await start_cron_jobs() # Start background scheduled tasks
                LOGGER.info("Cron jobs started.")
            except Exception as e:
                LOGGER.error(f"Error starting cron jobs: {e}", exc_info=True)
                # Log and maybe raise if cron jobs are essential

            # --- Remove Lock File (Successful Startup) ---
            LOGGER.info("Bot initialization complete. Removing lock file.")
            try:
                os.remove(Config.LOCKFILE)
                LOGGER.info(f"Lock file {Config.LOCKFILE} removed.")
            except OSError as e:
                LOGGER.error(f"Error removing lock file {Config.LOCKFILE} after successful startup: {e}", exc_info=True)
                # Log warning, but proceed as bot is running

            # --- Run the Bot Idle ---
            running_message = "Bot is now running and idle."
            if messages:
                try:
                    running_message = messages.get("main", "BOT_RUNNING")
                except Exception as e:
                     LOGGER.error(f"Error getting bot running message string: {e}", exc_info=True)
            LOGGER.info(running_message)
            await idle() # Keep the bot running until stopped (e.g., by signal)
            LOGGER.info("idle() finished. Bot is likely shutting down.")

        else:
            # --- Log Check Failed ---
            LOGGER.error(f"Log channel check failed. The LOGS_CHANNEL ({Config.LOGS_CHANNEL}) might be invalid or the bot lacks permissions.")
            # Attempt to notify the owner
            LOGGER.info(f"Attempting to notify BOT_OWNER ({Config.BOT_OWNER}) about the log check failure.")
            owner_notification_text = f"Log check failed for LOGS_CHANNEL {Config.LOGS_CHANNEL}" # Default
            if messages:
                try:
                    owner_notification_text = messages.get("main", "WRONG_LOG", None, Config.LOGS_CHANNEL)
                    LOGGER.info("Retrieved localized log failure message for owner.")
                except Exception as e:
                    LOGGER.error(f"Error getting owner notification message string: {e}", exc_info=True)
            else:
                LOGGER.warning("Messages object not available, using default owner notification message.")

            try:
                await unzipbot_client.send_message(
                    chat_id=Config.BOT_OWNER,
                    text=owner_notification_text
                )
                LOGGER.info(f"Notification sent to BOT_OWNER ({Config.BOT_OWNER}).")
            except Exception as e:
                LOGGER.error(f"Failed to send notification to BOT_OWNER ({Config.BOT_OWNER}): {e}", exc_info=True)
                # Log the error, but proceed with shutdown

            # --- Clean up Lock File on Failed Log Check ---
            LOGGER.info("Removing lock file due to failed log check...")
            try:
                if os.path.exists(Config.LOCKFILE):
                    os.remove(Config.LOCKFILE)
                    LOGGER.info(f"Lock file {Config.LOCKFILE} removed.")
                else:
                    LOGGER.info("Lock file already removed or doesn't exist.")
            except OSError as e:
                 LOGGER.error(f"Error removing lock file {Config.LOCKFILE} after failed log check: {e}", exc_info=True)

            # --- Initiate Shutdown (Log Check Failed) ---
            LOGGER.info("Initiating shutdown due to failed log check.")
            await async_shutdown_bot()

    # --- General Exception Handling for `main` ---
    except Exception as e:
        # Log the main loop error message
        error_main_loop_text = f"An unexpected error occurred in the main execution loop: {e}"
        if messages:
            try:
                error_main_loop_text = messages.get("main", "ERROR_MAIN_LOOP", None, e)
            except Exception as msg_e:
                LOGGER.error(f"Error getting main loop error message string: {msg_e}", exc_info=True)
        LOGGER.critical(error_main_loop_text, exc_info=True) # Use critical level for top-level errors

        # --- Ensure Lock File Cleanup on Error ---
        LOGGER.info("Attempting cleanup after error in main loop...")
        try:
            if os.path.exists(Config.LOCKFILE):
                LOGGER.info(f"Removing lock file {Config.LOCKFILE} due to error...")
                os.remove(Config.LOCKFILE)
                LOGGER.info("Lock file removed.")
                lock_file_removed_on_error = True
            else:
                 LOGGER.info("Lock file does not exist during error cleanup.")
        except OSError as lock_err:
            LOGGER.error(f"Error removing lock file {Config.LOCKFILE} during error handling: {lock_err}", exc_info=True)

        # --- Initiate Shutdown After Error ---
        LOGGER.info("Initiating shutdown following error in main loop.")
        await async_shutdown_bot()

    # --- Final Cleanup (Always Runs) ---
    finally:
        LOGGER.info("Entering final cleanup block for main function.")
        # Ensure lock file is removed if it wasn't already handled by error block
        if not lock_file_removed_on_error:
             LOGGER.info(f"Final check for lock file {Config.LOCKFILE}...")
             try:
                 if os.path.exists(Config.LOCKFILE):
                     LOGGER.warning(f"Lock file {Config.LOCKFILE} still exists in finally block. Removing it.")
                     os.remove(Config.LOCKFILE)
                     LOGGER.info("Lock file removed in finally block.")
                 else:
                     LOGGER.info("Lock file confirmed not present in finally block.")
             except OSError as e:
                 LOGGER.error(f"Error removing lock file {Config.LOCKFILE} in finally block: {e}", exc_info=True)

        # Ensure the client shutdown is attempted if `idle()` was exited cleanly or if an error occurred *before* shutdown was called
        # Note: async_shutdown_bot() might have already been called by signal handlers or error paths.
        # Checking client status might be useful, but calling stop() again is generally safe.
        LOGGER.info("Ensuring bot shutdown is complete in finally block.")
        # Avoid calling shutdown again if it was already called, e.g., after log check failure or main loop error.
        # We rely on the `idle()` ending or signals/errors triggering the shutdown.
        # If the process reaches here without `async_shutdown_bot` having been called
        # (e.g. `idle()` somehow returned without signal), we *should* call it.
        # However, a simple log message is safer than potentially complex state checking.
        LOGGER.info("Main function execution finished or aborted.")


# --- Script Entry Point ---
if __name__ == "__main__":
    # This block executes when the script is run directly
    LOGGER.info("Script starting execution...")
    try:
        # Run the main asynchronous function using the Pyrogram client's run method
        # This handles starting the asyncio event loop and running the provided coroutine
        LOGGER.info("Handing control to Pyrogram client's run method with main() coroutine.")
        unzipbot_client.run(main())
        LOGGER.info("Pyrogram client run method finished.") # This line is reached after shutdown
    except Exception as e:
        # Catch any exception that might occur during client.run() itself, although most should be caught within main()
        LOGGER.critical(f"A critical error occurred outside the main() function during client.run(): {e}", exc_info=True)
        # Potentially perform minimal cleanup here if possible, e.g., forceful lock file removal
        try:
             if os.path.exists(Config.LOCKFILE):
                 os.remove(Config.LOCKFILE)
                 LOGGER.info("Forcefully removed lock file after client.run() failure.")
        except Exception as final_err:
             LOGGER.error(f"Could not remove lock file during final error handling: {final_err}")
    finally:
         LOGGER.info("Script execution finished.")