> # Trello Salesforce Integration
>
> Syncs trello cards to Salesforce Tasks that live under the Account that matches the containing board in trello of the card
>
>
> ## TO RUN ON YOUR LOCAL MACHINE:
>
> `$git clone <thisURL> .`
>
> `$virtualenv -p python3.5 venv `
>
>
> ## Install Python deps from requirements.txt file:
>
> `$pip install -r requirements.txt`
>
>
> ## Set env vars in a .env file:
>
> `source venv/bin/activate`<br>
`export SFAPI_CONSUMER_KEY="xxx"`<br>
`export SFAPI_CONSUMER_SECRET="xxx"`<br>
>
> or put these lines in a .env file so they're set when you cd into the project directory <br>
> (you'll need autoenv installed to automatically set the env vars like this: <br>
> https://github.com/kennethreitz/autoenv)
>
>
> ## Start server: <br>
> `$python manage.py runserver`
