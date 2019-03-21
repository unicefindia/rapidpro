class ImiMobileException(Exception):  # pragma: needs cover
    pass


class ImiMobileResponse(object):  # pragma: needs cover
    DOC_START = '<?xml version="1.0" encoding="UTF-8"?><vxml version = "2.1">'
    DOC_START += '<property name="confidencelevel" value="0.5" />'
    DOC_START += '<property name="maxage" value="30" />'
    DOC_START += '<property name="inputmodes" value="dtmf" />'
    DOC_START += '<property name="interdigittimeout" value="12s"/>'
    DOC_START += '<property name="timeout" value="12s" />'
    DOC_START += '<property name="termchar" value="#"></property>'
    DOC_START += '<var name="recieveddtmf" />'

    DOC_START += '<var name="ExecuteVXML" />'
    DOC_START += '<form id="AcceptDigits">'
    DOC_START += '<var name="ExecuteVXML" />'
    DOC_START += '<var name="nResult" />'
    DOC_START += '<var name="nResultCode" expr="0" />'

    def __init__(self, **kwargs):
        self.document = self.DOC_START

    def __str__(self):
        if self.document.find("</form></vxml>") > 0:
            return self.document
        return self.document + "</form></vxml>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def join(self, response):
        self.document = self.document.replace(self.DOC_START, response.document)
        return self

    def say(self, text, **kwargs):
        result = '<prompt bargein="false">' + text + "</prompt>"
        self.document += result
        return self

    def play(self, url=None, digits=None, **kwargs):
        if url is None and digits is None:
            raise ImiMobileException("Please specify either a url or digits to play.")

        result = ""
        if digits:
            result += '<block><prompt bargein="false">' + digits + "</prompt></block>"

        if url:
            result += '<block><prompt bargein="false"><audio src="' + url + '" /></prompt></block>'

        self.document += result
        return self

    def pause(self, **kwargs):
        result = '<block><prompt bargein="false"><break '
        if kwargs.get("length", False):
            result += 'time="' + str(kwargs.get("length")) + 's"'

        result += "/></prompt></block>"

        self.document += result
        return self

    def redirect(self, url=None, **kwargs):
        result = '<subdialog src="' + url + '" ></subdialog>'

        self.document += result
        return self

    def hangup(self, **kwargs):
        result = "<exit />"
        self.document += result
        return self

    def reject(self, reason=None, **kwargs):
        self.hangup()
        return self

    def gather(self, **kwargs):
        result = '<field name="Digits" type="digits'

        if kwargs.get("num_digits", False):
            result += "?length=1"
        else:
            result += "?length=30"

        result += '">'

        if kwargs.get("action", False):
            method = kwargs.get("method", "post")
            result += "<filled>"
            result += '<log> Digits Value:: <value expr="Digits" /> </log>'
            result += '<assign name="recieveddtmf" expr="Digits" />'
            result += '<log> recieveddtmf ::  <value expr="recieveddtmf" /> </log>'
            result += (
                '<data name="RespJSON" src="'
                + kwargs.get("action")
                + '"  namelist="recieveddtmf" method="'
                + method
                + '" enctype="application/json" />'
            )
            result += '<log>ExecuteVXML ::<value expr="RespJSON" /></log>'

            result += '<assign expr="JSON.parse(RespJSON).result" name="nResultCode" />'
            result += '<log>Response Code: <value expr="nResultCode" /></log>'

            result += "<if cond=\"nResultCode === '1'\">"
            result += "<log>This is get method API</log>"
            result += "<log>Success Response Code Received. Moving to Next VXML</log>"
            result += '<goto next="' + kwargs.get("action") + '" />'
            result += "<else>"
            result += '<log>Invalid Response Code Received ::<value expr="nResultCode" /></log>'
            result += "</else>"
            result += "</if>"
            result += "</filled>"

        result += "</field>"
        self.document += result
        return self

    def record(self, **kwargs):
        result = '<record name="UserRecording" beep="true" '
        if kwargs.get("max_length", False):
            result += 'maxtime="' + str(kwargs.get("max_length")) + 's" '

        result += 'finalsilence="4000ms" dtmfterm="true" type="audio/x-wav">'

        if kwargs.get("action", False):
            method = kwargs.get("method", "post")
            result += (
                '<filled><log>Input received</log><data src="' + kwargs.get("action") + '" method="' + method + '" '
            )
            result += 'enctype="application/xml" /><goto next="#ExecuteVXML"/></filled>'

        result += "</record>"

        self.document += result
        return self
