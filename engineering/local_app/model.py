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


class OllamaResponse(BoundedResponse):
    def read(self):
        body=json.loads(super().read())
        if (not isinstance(body,dict) or body.get('done') is not True
                or body.get('done_reason')=='length'
                or not isinstance(body.get('message'),dict)
                or not isinstance(body['message'].get('content'),str)
                or not body['message']['content'].strip()):
            raise ModelGatewayError('Ollama returned an incomplete or invalid response')
        return json.dumps({'choices':[{'message':{'content':body['message']['content']}}]}).encode()


def thinking_setting(value):
    if value in (None,'','default'):return None
    if value=='false':return False
    if value=='true':return True
    raise ValueError('ENGINEER_OS_LOCAL_THINK must be default, false or true')


class LocalModel:
    def __init__(self,origin='http://127.0.0.1:11434',model='qwen3:8b',key='',*,provider='ollama',thinking=None,timeout=180):
        try:self.origin=local_url(origin)
        except IntegrationError as exc:raise ValueError(str(exc)) from None
        if not isinstance(model,str) or not model.strip() or len(model)>200:raise ValueError('Invalid model')
        if provider not in {'ollama','openwebui'}:raise ValueError('Provider must be ollama or openwebui')
        if thinking is not None and type(thinking) is not bool:raise ValueError('Thinking must be a boolean or None')
        if thinking is not None and provider!='ollama':raise ValueError('Explicit thinking control requires the Ollama provider')
        if type(timeout) is not int or not 1<=timeout<=600:raise ValueError('Timeout must be 1–600 seconds')
        self.timeout=timeout
        self.provider=provider
        self.thinking=thinking
        self.model=model;self.key=key;self.opener=build_opener(ProxyHandler({}),NoRedirect())
        def open_bounded(req,timeout):
            timeout=self.timeout
            if self.provider=='openwebui':req=Request(self.origin+'/api/chat/completions',data=req.data,headers=dict(req.header_items()),method='POST')
            if self.thinking is not None:
                original=json.loads(req.data)
                payload=dict(model=original['model'],messages=original['messages'],stream=False,
                             think=self.thinking,options=dict(temperature=original['temperature']))
                req=Request(self.origin+'/api/chat',data=json.dumps(payload,ensure_ascii=False).encode(),headers=dict(req.header_items()),method='POST')
                return OllamaResponse(self.opener.open(req,timeout=timeout))
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
            state='MODEL_LISTED' if available else 'MODEL_MISSING'
        except (OSError,ValueError,TypeError,AttributeError):available=False;state='SERVICE_UNAVAILABLE'
        return dict(available=available,state=state,inference_verified=False,model=self.model,origin=self.origin,provider=self.provider,thinking=self.thinking,timeout=self.timeout,note={'MODEL_LISTED':'Модель найдена; выполнение запроса ещё не проверено.','MODEL_MISSING':'Сервер отвечает, но выбранная модель отсутствует.','SERVICE_UNAVAILABLE':'Сервер модели недоступен или вернул неверный ответ.'}[state])

    def checkpoint_identity(self):
        if self.provider!='ollama':return None
        from .analysis_identity import digest
        headers={'Accept':'application/json'}
        if self.key:headers['Authorization']='Bearer '+self.key
        try:
            with self.opener.open(Request(self.origin+'/api/tags',headers=headers),timeout=2) as response:
                body=json.loads(BoundedResponse(response).read())
            matches=[m for m in body.get('models',[]) if m.get('name')==self.model or m.get('model')==self.model]
            if len(matches)!=1 or not isinstance(matches[0].get('digest'),str) or not matches[0]['digest']:return None
            req=Request(self.origin+'/api/show',data=json.dumps(dict(model=self.model)).encode(),headers=dict(headers,**{'Content-Type':'application/json'}),method='POST')
            with self.opener.open(req,timeout=2) as response:show=json.loads(BoundedResponse(response).read())
            if not isinstance(show,dict) or 'parameters' not in show:return None
            config={k:show.get(k) for k in ('parameters','template','system','model_info')}
            return dict(provider=self.provider,origin=self.origin,model=self.model,model_digest=matches[0]['digest'],
                        config_sha256=digest(config),thinking=self.thinking,temperature=0,timeout=self.timeout,response_chars=32000)
        except (OSError,ValueError,TypeError,AttributeError):return None
