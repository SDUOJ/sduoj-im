# sduoj-im

SDUOJ-based real-time communication system with pluggable components for in-depth support of course needs, unified establishment of WebSocket for the entire system, supporting real-time tutoring for teaching assistants, enabling private and group chat communication, and facilitating real-time notification broadcasting and other functions. Use FastAPI as the backend, Python 3.12.

## Deploy

**1. Update const.py as reality：** <br>
Changing the contents in the const file to your own content


**2. Installing the required environment：**

```shell
python -m venv venv
venv\Scripts\activate(Windows)
source venv/bin/activate(Linux/MacOS)
pip install -r requirements.txt
```

**3. Establishment of the database：**
```shell
python db_init.py
```

**4. Start the project：**
```shell
mkdir logs
python -m gunicorn -c gunicorn.conf.py main:app
```

## Acknowledgment
We acknowledge the utilization of ERICommiter, developed by Pengyu Xue, Linhao Wu et al., for commit message generation by the SDUOJ team from July 1 to September 1, 2024. We express our gratitude for this contribution.
