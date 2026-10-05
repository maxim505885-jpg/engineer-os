"""Safe loopback-only wrapper around the existing model gateway."""
import json
from urllib.request import build_opener,ProxyHandler,HTTPRedirectHandler,Request
from engineering.integrations.local_http import local_url,IntegrationError
from engineering.model_gateway.openai_compatible import OpenAICompatibleGateway,ModelGatewayError


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


class BoundedResponse:
    def __init__(self,response):self.response=response
    def __enter__(self):return self
    def __exit__(self,*args):self.response.close()
    def read(self):
        raw=self.response.read(2*1024*1024+1)
        if len(raw)>2*1024*1024:raise ModelGatewayError('Model response exceeds 2 MiB')
        return raw


class LocalModel:
    def __init__(self,origin='http://127.0.0.1:11434',model='qwen3:8b',key='',*,provider='ollama'):
        try:self.origin=local_url(origin)
        except IntegrationError as exc:raise ValueError(str(exc)) from None
        if not isinstance(model,str) or not model.strip() or len(model)>200:raise ValueError('Invalid model')
        if provider not in {'ollama','openwebui'}:raise ValueError('Provider must be ollama or openwebui')
        self.provider=provider
        self.model=model;self.key=key;self.opener=build_opener(ProxyHandler({}),NoRedirect())
        def open_bounded(req,timeout):
            if self.provider=='openwebui':req=Request(self.origin+'/api/chat/completions',data=req.data,headers=dict(req.header_items()),method='POST')
            return BoundedResponse(self.opener.open(req,timeout=timeout))
        self.gateway=OpenAICompatibleGateway(self.origin,api_key=key or None,opener=open_bounded)

    def chat(self,messages):
        try:result=self.gateway.chat(model=self.model,messages=tuple(messages))
        except (ModelGatewayError,OSError,ValueError) as exc:raise RuntimeError('Local model unavailable or returned an invalid response. Check Ollama/Open WebUI and model settings.') from None
        if len(result)>32000:raise RuntimeError('Model reply exceeds 32,000 characters')
        return result

    def health(self):
        from urllib.request import Request
        headers={'Accept':'application/json'}
        if self.key:headers['Authorization']='Bearer '+self.key
        try:
            with self.opener.open(Request(self.origin+('/api/models' if self.provider=='openwebui' else '/v1/models'),headers=headers),timeout=2) as response:raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:raise ValueError
            body=json.loads(raw)
            available=any(isinstance(x,dict) and x.get('id')==self.model for x in body.get('data',[]))
        except (OSError,ValueError,TypeError,AttributeError):available=False
        return dict(available=available,model=self.model,origin=self.origin,provider=self.provider,note='Model listed; inference not yet verified.' if available else 'Start the local model service and check the configured model.')
