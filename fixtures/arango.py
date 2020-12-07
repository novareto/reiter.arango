from typing import NamedTuple


class Config(NamedTuple):
    url: str
    user: str
    password: str
    database: str


@pytest.fixture(scope="session")
def arangodb(request):
    """Create a intermediary docker container a arangodb instance
    """
    import docker
    import time

    arango_url = request.config.getoption("--arango_url")
    arango_user = request.config.getoption("--arango_user")
    arango_password = request.config.getoption("--arango_password")
    arango_database = request.config.getoption("--arango_database")

    client = docker.from_env()
    config = Config(
        user=arango_user,
        password=arango_password,
        database=arango_database,
        url=arango_url,
    ))

    container = client.containers.run(
        image="arangodb/arangodb:3.7.3",
        environment={
            "ARANGO_ROOT_PASSWORD": config.arango.password
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
    return database


def pytest_addoption(parser):

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
        "--arango_url", action="store", default="http://192.168.52.2:8529",
        help="arango_url: arango database url"
    )
