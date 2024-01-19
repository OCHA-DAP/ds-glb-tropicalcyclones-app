# Global Tropical Cyclones App

## About

App showing global analysis of tropical cyclones return period,
for anticipatory action trigger design or monitoring.
For analysis behind the datasets in the app, see the
`ds-glb-tropicalcyclones` repository.

## Usage

### Running the app

To run the app, run the following command:

```bash
python app.py
```

### Migrating data

The data for this app is stored in the repository, as opposed to in
`AA_DATA_DIR`. To migrate the relevant datasets into the repository data
directory from the `AA_DATA_DIR`, run the following command:

```bash
python migrate_data.py
```
