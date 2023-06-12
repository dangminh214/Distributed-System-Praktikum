class HTTPParser:
    def __init__(self): # Attribute initialisieren
        self.method = None
        self.path = None
        self.version = None
        self.headers = {}
        self.body = None

    def parse(self, lines): # Liste von Zeichenfolgen - HTTP-Anfrage
        # Get the request line
        request_line = lines[0].split(' ') #  erste Zeile wird aufgespalten
        self.method = request_line[0]
        self.path = request_line[1]
        self.version = request_line[2]

        # Get the headers
        for line in lines[1:]: # Headers werden analysiert ab der zweiten Zeile
            headerPair = line.split(': ', 1) # Jede Zeile wird anhand des Trennzeichens ': ' in den Schlüssel-Wert-Paar aufgeteilt
            if line == '' or len(headerPair) <= 1:
                break  # Leere Zeile zeigt das Ende der Header an
            key, value = headerPair
            self.headers[key] = value

        # Get the body if present
        if len(lines) > 1:
            self.body = lines[-1]
