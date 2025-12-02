Research Project / Federated Machine learning
## Install dependencies and project

The dependencies are listed in the `pyproject.toml` and they can installed as follows:

```bash
pip install -e .
```

> **Note:** Your `pyproject.toml` file can define more than just the dependencies of your Flower app. It specifies hyperparameters for the runs and control which Flower Runtime is used. By default, it uses the Simulation Runtime, but it can switch to the Deployment Runtime when needed.
> More info can be seen here: [TOML configuration guide](https://flower.ai/docs/framework/how-to-configure-pyproject-toml.html).

## Run with the Simulation Engine

In the `app-research-project` directory, use `flwr run` to run a local simulation:

```bash
flwr run .
```
Or feel free to use any of the current python codes to run specific scenarios (different number of clients across multiple seeds, different data distributions, and even different partial client participation. For this use (example):
```bash
python results_clients_withoutSEEDS.py.
```
**Note:** Its important that you are indise the correct repository to run the python codes!

Once you run any of the files that start with "results......py", the simulated data will be saved inside the "results" folder. This data can be visualized by running the codes inside the python plotting folder. The plots will be later saved in "plots" folder.
