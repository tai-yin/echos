import pytest
from subprocess import Popen, PIPE

def test_samcli_cli():
    Popen(["sam", "build"], stdout=PIPE, stderr=PIPE)