# An ARCHIGNES fork of Pongo's [simplicity](https://github.com/PongoAI/simplicity)

Original README:

```
# An Open source version of perplexity

- Exa for web searches
- [Pongo](https://joinpongo.com) for semantic filtering
- llama3 hosted on Together.xyz
```

It took me 17 minutes to get it running locally. I already had the Together and Exa API keys.

<em>A demo search of [How fast can an elephant run?], run locally.</em>

<img src="https://github.com/archignes/forked-simplicity/assets/6070690/44a57b0d-b3db-4a0e-97be-16ceef9db67f" alt="Demo search of How fast can an elephant run?" width="500" height="300">


## Setup

### 1. Get API keys and add to your environment.

See here:
```
exa_client = Exa( os.environ.get("EXA_API_KEY"))
openai_client = OpenAI(api_key=os.environ.get("TOGETHER_API_KEY"), base_url='https://api.together.xyz/v1')
pongo_client = pongo.PongoClient(os.environ.get("PONGO_API_KEY"))
```

Pongo: https://www.pongo.ai/onboarding/code-and-keys

Then:

```
export PONGO_API_KEY="{pongo_api_key}"
```

### 2. Frontend

```
cd frontend
npm install
npm run start
```


### 3. Backend

```
p -m venv
source venv/bin/activate
p -m pip install -r requirements.txt
p -m uvicorn main:app --reload
```

