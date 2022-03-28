import datetime
import logging
import os
import azure.functions as func

from .service_data_processor.processor import ServiceDataProcessor


def main(TestTrigger: func.TimerRequest) -> None:
    """Azure Function to process service data for the service matcher's needs.
    
    Triggered by scheduled timer every night.

    Args:
        TestTrigger (func.TimerRequest)
    """
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if TestTrigger.past_due:
        logging.info('The timer is past due!')

    logging.info("Running service data processor {}".format(utc_timestamp))
    service_data_processor = ServiceDataProcessor()
    service_data_processor.process_service_descriptions()
    service_data_processor.process_service_classes()

    utc_timestamp2 = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    logging.info("Finished running service data processor {}".format(utc_timestamp2))

    logging.info('Python timer trigger function ran at %s', utc_timestamp2)
