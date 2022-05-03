## How To Contribute
- Fork the repo and clone to your local machine
- cd into project folder and create a virtual environment using `virtualenv` if you don't have it installed you can install it using the following command:
```bash
pip install virtualenv
```
Once installed you can create a new virtual environment using the command :
```bash
virtualenv <env name>
```
- Activate the virtual environment as follows:
```bash
source env/bin/activate
```
or on windows
```bash
.\<env name>\scripts\activate
```

- Next install the required dependencies for the project using the `requirements.txt` file, as follows:

```bash
pip install -r requirements.txt
```

- Once you have done this you can run the bot from `main.py` as follows:

```bash
python main.py
```

- Test the bot out with your config variables, and add your changes as you deem fit on a separate branch.
- Push to your forked repo and then send a PR with the description of the changes you added.

### Coming Soon
- Unique business link for direct access to a particular store's catalogue
- search for businesses by name
- cart functionality
