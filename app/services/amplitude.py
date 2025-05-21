from typing import Dict, Any, Optional, List, Union
import logging
from amplitude import Amplitude, BaseEvent

from app.models.track import AnalyticsTrackBase


class AmplitudeTracker:
    """
    A simple class for tracking events with the Amplitude Python SDK.
    """

    def __init__(self, user_id: Optional[str] = None, device_id: Optional[str] = None):
        """
        Initialize the AmplitudeTracker.

        Args:
            user_id: Optional default user ID for events
            device_id: Optional default device ID for events
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)

        try:
            # Store API key and configuration
            self.api_key = 'd68af844f7a681f8f9364981097737fb'
            self.user_id = user_id
            self.device_id = device_id

            # Log initialization
            self.logger.info(f"Initializing AmplitudeTracker with API key: {self.api_key[:4]}...")

            # Initialize Amplitude client
            self.client = Amplitude(self.api_key)
            self.client.use_batch = True
            self.client.configuration.flush_queue_size = 1000

            # Set timeouts to avoid hanging
            self.client.configuration.connection_timeout = 10.0  # Add reasonable timeout

            if user_id:
                self.client.configuration.user_id = user_id
                self.logger.debug(f"Default user_id set: {user_id}")

            if device_id:
                self.client.configuration.device_id = device_id
                self.logger.debug(f"Default device_id set: {device_id}")

            self.logger.info("AmplitudeTracker initialized successfully")

        except ImportError as ie:
            self.logger.error(f"Failed to import amplitude package: {str(ie)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize AmplitudeTracker: {str(e)}")
            raise

    def track(self,
              event_type: str,
              user_id: Optional[str] = None,
              device_id: Optional[str] = None,
              event_properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track a single event to Amplitude.
        """
        try:
            # Determine effective IDs
            effective_user_id = user_id or self.user_id
            effective_device_id = device_id or self.device_id

            self.logger.debug(f"Tracking event: {event_type}")

            if not effective_user_id and not effective_device_id:
                self.logger.warning("Neither user_id nor device_id is set for this event")
                # Generate a random device_id if needed
                import uuid
                effective_device_id = str(uuid.uuid4())
                self.logger.debug(f"Generated random device_id: {effective_device_id}")

            # Create and send event
            event = BaseEvent(
                event_type=event_type,
                user_id=effective_user_id,
                device_id=effective_device_id,
                event_properties=event_properties or {}
            )

            # Log event details for debugging
            self.logger.debug(f"Event details: type={event_type}, " +
                              f"user_id={effective_user_id}, device_id={effective_device_id}, " +
                              f"properties_count={len(event_properties or {})}")

            self.client.track(event)
            return True

        except Exception as e:
            self.logger.error(f"Exception sending event to Amplitude: {str(e)}", exc_info=True)
            return False

    def track_events(self, events: List[AnalyticsTrackBase]) -> bool:
        """
        Track multiple events to Amplitude.

        Args:
            events: List of event dictionaries with event_type and optional properties

        Returns:
            bool: True if the events were sent successfully, False otherwise
        """
        if not events:
            self.logger.warning("No events provided to track_events")
            return False

        self.logger.info(f"Starting to track {len(events)} events")

        # Log sample event for debugging
        if events:
            try:
                sample = events[0]
                self.logger.debug(f"Sample event: event_name={getattr(sample, 'event_name', None)}, " +
                                  f"identity={getattr(sample, 'identity', None)}")

                # Check if event_name exists on all events
                missing_names = sum(1 for e in events if not getattr(e, 'event_name', None))
                if missing_names:
                    self.logger.warning(f"{missing_names} events are missing event_name")
            except Exception as e:
                self.logger.error(f"Error examining events: {str(e)}")

        successful = 0
        try:
            for i, event_data in enumerate(events):
                try:
                    # Get event type (name)
                    event_type = getattr(event_data, 'event_name', None)
                    if not event_type:
                        self.logger.warning(f"Skipping event at index {i} without event_name")
                        continue

                    # Extract user and device IDs
                    user_id, device_id = self.extract_ids_from_event(event_data)

                    # Ensure we have at least one ID
                    if not user_id and not device_id:
                        self.logger.warning(f"Event {i} ({event_type}) has neither user_id nor device_id")
                        # Generate a random device ID as fallback
                        import uuid
                        device_id = str(uuid.uuid4())
                        self.logger.debug(f"Generated random device_id for event {i}: {device_id}")

                    # Get event properties safely
                    event_properties = {}
                    if hasattr(event_data, 'event_data') and event_data.event_data:
                        event_properties = event_data.event_data

                    # Create the event
                    event = BaseEvent(
                        event_type=event_type,
                        user_id=user_id,
                        device_id=device_id,
                        event_properties=event_properties
                    )

                    # Track the event
                    self.client.track(event)
                    successful += 1

                except Exception as event_error:
                    # Log the error but continue processing other events
                    self.logger.error(f"Error processing event at index {i}: {str(event_error)}")
                    continue

            # Log success
            self.logger.info(f"Successfully tracked {successful}/{len(events)} events")
            return successful > 0

        except Exception as e:
            self.logger.error(f"Failed to track events batch: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def extract_ids_from_event(event: AnalyticsTrackBase):
        """
        Extract user_id and device_id from an event.

        Returns:
            tuple: (user_id, device_id)
        """
        # Default return values
        user_id, device_id = None, None

        try:
            # Safely get identity data
            identity = getattr(event, 'identity', None)

            if identity is None:
                return None, None

            # Check if identity is a dict
            if not isinstance(identity, dict):
                logging.getLogger(__name__).warning(
                    f"Event identity is not a dict: {type(identity)}"
                )
                return None, None

            # Get amplitude-specific identity info
            amplitude_info = identity.get('amplitude')

            if amplitude_info and isinstance(amplitude_info, dict):
                user_id = amplitude_info.get('user_id')
                device_id = amplitude_info.get('device_id')

        except Exception as e:
            logging.getLogger(__name__).error(f"Error extracting IDs: {str(e)}")

        return user_id, device_id

    def identify(self,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 user_properties: Dict[str, Any] = None) -> bool:
        """
        Send user properties to Amplitude.
        """
        try:
            effective_user_id = user_id or self.user_id
            effective_device_id = device_id or self.device_id

            if not effective_user_id and not effective_device_id:
                self.logger.error("Identify failed: Neither user_id nor device_id is provided")
                return False

            if not user_properties:
                self.logger.error("Identify failed: No user_properties provided")
                return False

            self.logger.debug(f"Identifying user: user_id={effective_user_id}, device_id={effective_device_id}")

            # Create identify event
            identify = self.client.identify()

            if effective_user_id:
                identify.user_id = effective_user_id

            if effective_device_id:
                identify.device_id = effective_device_id

            # Process operations
            ops_count = 0
            for op_type in ["$set", "$setOnce", "$add", "$append", "$prepend"]:
                if op_type in user_properties:
                    for key, value in user_properties[op_type].items():
                        if op_type == "$set":
                            identify.set(key, value)
                        elif op_type == "$setOnce":
                            identify.set_once(key, value)
                        elif op_type == "$add":
                            identify.add(key, value)
                        elif op_type == "$append":
                            identify.append(key, value)
                        elif op_type == "$prepend":
                            identify.prepend(key, value)
                        ops_count += 1

            self.logger.debug(f"Applied {ops_count} property operations")

            # Send the identify event
            self.client.identify(identify)
            self.logger.info("Identify event sent successfully")
            return True

        except Exception as e:
            self.logger.error(f"Exception sending identify event: {str(e)}", exc_info=True)
            return False

    def flush(self) -> bool:
        """
        Immediately send any queued events to Amplitude servers.

        Returns:
            bool: True if the flush was successful, False otherwise
        """
        try:
            self.logger.info("Flushing events to Amplitude...")
            result = self.client.flush()
            self.logger.info(f"Flush completed with result: {result}")
            return True
        except Exception as e:
            self.logger.error(f"Exception flushing events: {str(e)}", exc_info=True)
            return False
