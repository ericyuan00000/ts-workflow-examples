import os
import toml
import logging
import jobflow as jf
from ase.io import read
from quacc import get_settings
from quacc.recipes.newtonnet.ts import ts_job, irc_job, geodesic_job

# Load configuration from TOML file
config = toml.load('inputs_using_newtonnet.toml')

# Constants from TOML file
REACTANT_XYZ_FILE = config['paths']['reactant']
PRODUCT_XYZ_FILE = config['paths']['product']
MODEL_PATH = config['paths']['model_path']
SETTINGS_PATH = config['paths']['settings_path']

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
settings.NEWTONNET_MODEL_PATH = os.getcwd() + MODEL_PATH
settings.NEWTONNET_CONFIG_PATH = os.getcwd() + SETTINGS_PATH
settings.WORKFLOW_ENGINE = 'jobflow'

# Calculation and optimization keyword arguments
calc_kwargs1 = {
    'hess_method': None,
}

def main():
    # Read reactant and product structures
    reactant = read(REACTANT_XYZ_FILE)
    product = read(PRODUCT_XYZ_FILE)
    logger.info("Successfully read reactant and product structures.")

    # Create NEB job
    job1 = geodesic_job(reactant, product, calc_kwargs=calc_kwargs1)
    logger.info("Created Geodesic job.")

    # Create TS job with custom Hessian
    job2 = ts_job(job1.output['highest_e_atoms'], use_custom_hessian=True, **calc_kwargs1)
    logger.info("Created TS job without custom Hessian.")

    # Create IRC job in forward direction
    job3 = irc_job(job2.output['atoms'], direction='forward', **calc_kwargs1)
    logger.info("Created IRC job in forward direction.")

    # Create IRC job in reverse direction
    job4 = irc_job(job2.output['atoms'], direction='reverse', **calc_kwargs1)
    logger.info("Created IRC job in reverse direction.")

    # Combine jobs into a flow
    jobs = [job1, job2, job3, job4]
    flow = jf.Flow(jobs)
    logger.info("Jobs combined into a flow.")

    # Execute the workflow locally
    responses = jf.managers.local.run_locally(flow)
    logger.info("Workflow executed successfully.")
    logger.info(f"Responses: {responses}")


if __name__ == "__main__":
    main()
