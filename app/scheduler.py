import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .services.batch_processor import data_processor
from .core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def start(self):
        # Schedule data refresh every 15 minutes
        self.scheduler.add_job(
            self.run_data_refresh,
            CronTrigger(minute=f"*/{settings.fetch_interval_minutes}"),
            id='data_refresh',
            name='Crypto Data Refresh',
            max_instances=1
        )
        
        # Schedule daily full data processing at 00:00 UTC
        self.scheduler.add_job(
            self.run_full_data_processing,
            CronTrigger(hour=0, minute=0),
            id='full_data_processing',
            name='Full Data Processing',
            max_instances=1
        )
        
        # Schedule weekly cleanup at Sunday 02:00 UTC
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_cleanup',
            name='Weekly Data Cleanup',
            max_instances=1
        )
        
        self.scheduler.start()
        logger.info("Data scheduler started")
        
        # Run initial data load
        await self.run_data_refresh()
        
        # Keep the scheduler running
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        finally:
            self.scheduler.shutdown()
    
    async def run_data_refresh(self):
        logger.info("Starting scheduled data refresh")
        try:
            await data_processor.process_cryptocurrency_data()
            await data_processor.process_defi_data()
            logger.info("Scheduled data refresh completed successfully")
        except Exception as e:
            logger.error(f"Error during scheduled data refresh: {e}")
    
    async def run_full_data_processing(self):
        logger.info("Starting full data processing")
        try:
            await data_processor.run_full_data_processing()
            logger.info("Full data processing completed successfully")
        except Exception as e:
            logger.error(f"Error during full data processing: {e}")
    
    async def cleanup_old_data(self):
        logger.info("Starting weekly data cleanup")
        try:
            from .core.database import clickhouse_manager
            
            # Remove data older than 1 year
            cleanup_queries = [
                "DELETE FROM price_history WHERE timestamp < (now() - INTERVAL 1 YEAR)",
                "DELETE FROM market_data WHERE timestamp < (now() - INTERVAL 1 YEAR)",
                "DELETE FROM tvl_history WHERE timestamp < (now() - INTERVAL 1 YEAR)",
                "OPTIMIZE TABLE price_history FINAL",
                "OPTIMIZE TABLE market_data FINAL",
                "OPTIMIZE TABLE tvl_history FINAL"
            ]
            
            for query in cleanup_queries:
                try:
                    clickhouse_manager.execute_query(query)
                    logger.info(f"Executed cleanup query: {query}")
                except Exception as e:
                    logger.error(f"Error executing cleanup query '{query}': {e}")
            
            logger.info("Weekly data cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during weekly cleanup: {e}")


async def main():
    scheduler = DataScheduler()
    await scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())