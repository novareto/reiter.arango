import arango
import pytest
from typing import NamedTuple


READY_PHRASE = (
    b"ArangoDB (version 3.7.3 [linux]) is ready for business. Have fun!\n"
)


class Config(NamedTuple):
    url: str
    user: str
    password: str
    database: str


@pytest.fixture(scope="session")
def arango_config(request):
    """Create a intermediary docker container a arangodb instance
    """
    import docker
    import time

    local = request.config.getoption("--localdb")
    arango_url = request.config.getoption("--arango_url")
    arango_user = request.config.getoption("--arango_user")
    arango_password = request.config.getoption("--arango_password")
    arango_database = request.config.getoption("--arango_database")

    if local:
        return Config(
            user=arango_user,
            password=arango_password,
            database=arango_database,
            url=arango_url or "http://localhost:8529",
        )

    if arango_url is not None:
        raise RuntimeError(
            "You can't specify an arango url if running non-local tests.")

    client = docker.from_env()
    config = Config(
        user=arango_user,
        password=arango_password,
        database=arango_database,
        url="http://192.168.52.2:8529",
    )

    container = client.containers.run(
        image="arangodb/arangodb:3.7.3",
        environment={
            "ARANGO_ROOT_PASSWORD": config.password
        },
        detach=True
    )

    ipam_pool = docker.types.IPAMPool(
        subnet='192.168.52.0/24',
        gateway='192.168.52.254'
    )

    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool]
    )

    mynet = client.networks.create(
        "network1",
        driver="bridge",
        ipam=ipam_config
    )

    mynet.connect(container, ipv4_address="192.168.52.2")

    while True:
        logs = container.logs()
        if logs.endswith(READY_PHRASE):
            break
        time.sleep(0.1)

    def cleanup():
        mynet.disconnect(container)
        mynet.remove()
        container.stop()
        container.remove()

    request.addfinalizer(cleanup)
    return config


@pytest.fixture(scope="session")
def arangodb(arango_config):

    client = arango.ArangoClient(arango_config.url)
    system_db = client.db(
        '_system',
        username=arango_config.user,
        password=arango_config.password
    )
    if not system_db.has_database(arango_config.database):
        system_db.create_database(arango_config.database)

    yield client.db(
        arango_config.database,
        username=arango_config.user,
        password=arango_config.password
    )
    system_db.delete_database(arango_config.database)


def pytest_addoption(parser):

    parser.addoption(
        "--localdb", action="store_true",
        help="arango: use a local instance of Arango or deploy a docker."
    )

    parser.addoption(
        "--arango_user", action="store", default="root",
        help="arango_user: name of the arango user"
    )

    parser.addoption(
        "--arango_password", action="store", default="openSesame",
        help="arango_password: arango password"
    )

    parser.addoption(
        "--arango_database", action="store", default="tests",
        help="arango_database: arango database"
    )

    parser.addoption(
        "--arango_url", action="store", default=None,
        help="arango_url: arango database url"
    )
