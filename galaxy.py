import os
import yaml

with open("galaxy.yml") as f:
    galaxy = yaml.safe_load(f)
galaxy["version"] = os.environ["GALAXY_VERSION"]
with open("galaxy.yml", "w") as f:
    yaml.safe_dump(galaxy, f)
