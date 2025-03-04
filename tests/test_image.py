import json

from pytest import fixture
from yellowbox.containers import create_and_pull, removing
from yellowbox.image_build import build_image


@fixture(scope="module", params=["2.*", "1.*"])
def poetry_version(request):
    return request.param


@fixture(scope="module")
def image(poetry_version, docker_client):
    image_name = f"test-project:{poetry_version}".replace(".*", "")

    with build_image(
        docker_client,
        image_name,
        path=".",
        dockerfile="tests/test-project/Dockerfile",
        buildargs={"POETRY_VERSION": poetry_version},
    ) as image:
        yield image


def test_update(docker_client, image):
    cntr = create_and_pull(docker_client, image, "poetry add types-retry@latest")
    with removing(cntr):
        cntr.start()
        assert cntr.wait()["StatusCode"] == 0
        logs = cntr.logs().decode()
    _, sep, rest = logs.partition("!!! PACKAGES CHANGED !!!")
    assert sep is not None, logs
    args = json.loads(rest)
    __, raw_change, raw_context = args
    changes = json.loads(raw_change)
    context = json.loads(raw_context)
    (change,) = changes
    assert change["package"] == "types-retry"
    assert context == {}
