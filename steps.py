"""Base step that runs a PNF simulator."""
import docker
import os
import yaml
import random
from requests import post
from json import loads
from onaptests.steps.base import BaseStep


# --------- utils
def get_config(config):
    """Read a config YAML file."""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir_path}/{config}", "r") as ymlfile:
        config = yaml.load(ymlfile)
    return config

def generate_id():
    return random.randint(10**3, 10**5)




# --------- STEP LEVEL 1

class SimInstanceStep(BaseStep):
    """Manage simulator containers."""


    def __init__(self, cleanup: bool, conf_name: str) -> None:
        super().__init__(cleanup=cleanup)
        self._client = docker.from_env()

        config = get_config(conf_name)
        self._client = docker.from_env()
        self._version = config.get('version', 'latest')
        self._registry = config.get('registry', '')
        self._image_name = config.get('image_name', '')
        self._name = config.get('name', '')


    @property
    def description(self) -> str:
        """Step description."""
        return "Run PNF simulator containers."

    @property
    def component(self) -> str:
        """Component name."""
        return "Environment"


    @property
    def image_ref(self):
        """Derive a full image reference."""
        reference = f'{self._registry}/{self._image_name}:{self._version}'
        if not all([self._registry, self._image_name]):
            raise ValueError(f"Image reference: {reference}.")
        return reference

    @property
    def name(self):
        """Get the container name (URL)."""
        if not self._name:
            raise ValueError("Container name has to be provided.")
        return self._name



    @BaseStep.store_state
    def execute(self) -> None:
        """Run a container from am image."""
        # get the image
        self._client.images.pull(repository=self.image_ref)

        # run a container
        self._client.containers.run(
            image=self.image_ref, detach=True, name=self.name)

    @BaseStep.store_state
    def cleanup(self) -> None:
        """Remove containers and images."""
        # cleanup a container
        container = self._client.containers.get(self.name)
        container.stop()
        container.remove()

        # cleanup an image
        self._client.images.remove(self.image_ref)




# --------- STEP LEVEL 2

class LaunchSimulatorStep(BaseStep):
    """Manage simulator containers."""




    def __init__(self, cleanup: bool, **config) -> None:
        super().__init__(cleanup=cleanup)
        self.add_step(SimInstanceStep(cleanup=cleanup))



    @property
    def description(self) -> str:
        """Step description."""
        return "Run PNF simulator containers."

    @property
    def component(self) -> str:
        """Component name."""
        return "Environment"


    @BaseStep.store_state
    def execute(self) -> None:
        """Run PNF simulator containers."""
        # get the image and container
        super().execute()
        # self.start()

    @BaseStep.store_state
    def cleanup(self) -> None:
        """Remove containers and images."""
        super().cleanup()

    # def start(self, config):
    #     req_headers = {
    #                     "Content-Type": "application/json",
    #                     "X-ONAP-RequestID": "123",
    #                     "X-InvocationID": "456"
    #                 }

    #     payload_location = config['start'].get('payload_location', '')
    #     with open(payload_location) as data:
    #         json_data = loads(data.read())
    #         sim_ip = 'localhost'
    #         sim_port = 8087
    #         sim_path = 'simulator'
    #         sim_response = post(
    #             f'{sim_ip}:{sim_port}/{sim_path}',
    #             headers=req_headers,
    #             json=json_data)
    #         sim_response.raise_for_status()




# --------- STEP LEVEL 0

class Network():
    def __init__(self, config = None):
        self._client = docker.from_env()
        self._id = generate_id()
        ipam_config = None

        if config:
            ipam_pool = docker.types.IPAMPool(
                subnet=config['ipam_pool'].get('subnet', None),
                gateway=config['ipam_pool'].get('gateway', None))
            ipam_config = docker.types.IPAMConfig(
                pool_configs=[ipam_pool],
                driver='default')

        self.network = self._client.networks.create(
            name=f"network-{self._id}",
            driver="bridge",
            ipam=ipam_config)

class Service():
    def __init__(self, image, network = None, config = None):
        self._client = docker.from_env()
        self._id = generate_id()

        self.service = self._image.create(
            name=f'service-{self._id}',
            image=image,
            networks=[network.id],  # TODO IPv4 address in the network
        )