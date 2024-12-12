import asyncio
import logging
import yaml
from azure_integration import AzureServices

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_azure_services():
    # Load configuration
    with open('config/base.yml', 'r') as f:
        config = yaml.safe_load(f)['AZURE']
    
    try:
        # Initialize Azure Services
        azure_services = AzureServices(config)
        logger.info("Azure Services initialized successfully")
        
        # Test secret retrieval
        test_secret_name = "test-secret"
        secret = await azure_services.get_secret(test_secret_name)
        if secret:
            logger.info(f"Successfully retrieved secret: {test_secret_name}")
        else:
            logger.warning(f"Could not retrieve secret: {test_secret_name}")
        
        # Test blob storage (with a sample byte string)
        test_container = "test-container"
        test_blob_name = "test-blob.txt"
        test_data = b"Hello, Azure Blob Storage!"
        
        blob_result = await azure_services.store_blob(test_container, test_blob_name, test_data)
        if blob_result:
            logger.info(f"Successfully stored blob: {test_blob_name} in container: {test_container}")
        else:
            logger.warning(f"Failed to store blob: {test_blob_name}")
    
    except Exception as e:
        logger.error(f"Error testing Azure services: {e}")

if __name__ == "__main__":
    asyncio.run(test_azure_services())
