# Backtesting Platform

This application is the backend code that runs the backtesting platform within the Algorithmic Trading Backtesting 
System. The other components of the system can be found here:
- [User Interface](https://github.com/JakeThomson/ATB_front-end)
- [Data Access API](https://github.com/JakeThomson/ATB_data-access-api)

The system was built entirely by me in 10 weeks for my final year project.
To find out more about this and other projects things I've worked on, check out my website
[jake-t.codes](https://jake-t.codes)!

## Installation
1. You will need Python 3.8+ installed and working on your system to run this project, download the recommended version 
[here](https://www.python.org/downloads/release/python-395/).
   
<span style="font-size:14pt;">**NOTE:**</span> If you are installing python for the first time, make sure you tick the 
`Add Python to PATH/environment variables` option.

2. Clone git repository onto your machine.
```
git clone https://github.com/JakeThomson/ATB_data-access-api
```

3. Go to project directory in cmd/terminal.
```
cd \path\to\project_directory\
```

4. Create a virtual environment in the directory for python to run in.
```
py -m venv ./venv
```

5. Activate the virtual environment
```
.\venv\Scripts\activate
```

6. Install all required python libraries to run the backtest.
```
pip install -r requirements.txt
```


## Running the application

To run the backtesting platform, navigate to the project directory in cmd/terminal and use the command
```
py main.py
```
If it is the first time running the application, it will need to download the required historical data - this will
take around 4-10 minutes depending on your download speed.

Once the platform is live, it can be viewed on the URL [algo-trader.jake-t.codes](https://algo-trader.jake-t.codes)

<span style="font-size:14pt;">**IMPORTANT:**</span> When you wish to stop the application, you must do so by pressing 
`ctrl` + `c`/`cmd` + `c` in the cmd/terminal window. This will allow the backtest to safely shut down.

If you wish for the backtest to connect to the data access API on a local network, then use the command 
```
py main.py local
```

