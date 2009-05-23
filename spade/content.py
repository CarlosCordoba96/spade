# encoding: UTF-8
from xmpp import simplexml
from exceptions import KeyError

def co2xml(map):
    """ Convenience recursive function for transforming ContentObjects into XML.  
        The transformation is {x:y} --> <x>y</x> """
    xml = ""
    for key, value in map.items():
        if "ContentObject" in str(type(value)):
            xml += "<%s>%s</%s>" % (key, co2xml(value), key)
        elif "list" in str(type(value)):
            for i in value:
                xml += "<%s>%s</%s>" % (key, i, key)
        elif value != None and value != "None":
            xml += "<%s>%s</%s>" % (key, value, key)
    return xml

class ContentObject(dict):
    """
    WARNING: copy.copy() does NOT work for this class :-?
    """
    def __init__(self, namespaces={}):
        dict.__init__(self)
        self.namespaces = namespaces

    def __setattr__(self, key, value):
        """
        Overloader of __setattr__ allows for entering keys in prefix:tag format
        without worry.
        """
        if not self.__dict__.has_key('_ContentObject__initialised'):
            return dict.__setattr__(self, key, value)
        elif self.__dict__.has_key(key):
            dict.__setattr__(self, key, value)
        else:
            #self.__setitem__(key, value)
            try:
                if ":" in key:
                    prefix,tag = key.rsplit(":")
                    if prefix not in self.namespaces:
                        # The usual FIPA namespace
                        if prefix == "fipa":
                            self.addNamespace("http://www.fipa.org/schemas/fipa-rdf0#", "fipa")
                        else:
                            self.addNamespace("",prefix)
            except:
                pass
            self.__setitem__(key, value)
                

    def __getattr__(self, name):
        try:
            return self[name]
        except:
            pass
        for ns in self.namespaces.values():
            try:
                return self[ns+name]
            except:
                pass
        # Ethical dilemma: Should ContentObject return a None when trying to
        # access a key that does not exist or should it raise an Exception?
        #raise KeyError
        return None
        
    def addNamespace(self, uri, abv):
        self.namespaces[uri] = abv
        return
        
    def pprint(self, ind=0):
        s = ""
        for k,v in self.items():
                try:
                        s = s + ('\t'*ind)+str(k)+":\n"+v.pprint(ind+1) + '\n'
                except:
                        s = s + ('\t'*ind)+str(k)+": " + str(v) + '\n'
        return s
    
    def asRDFXML(self):
        # Build rdf:RDF node
        root = simplexml.Node("rdf:RDF", {"xmlns:rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"})
        nss = {}
        for k,v in self.namespaces.items():
            if v in ["xml:","rdf:"]:
                pass
            elif v != None and v != "None":
                    nss["xmlns:"+v[:-1]] = k
        root.attrs.update(nss)
        root.addData("#WILDCARD#")
        return str(root).replace("#WILDCARD#",co2xml(self))


    """CAWEN DIOS!!!
        def asSL0(self):
            return toSL0(self)

def toSL0(self, data = None):
        
        self.co = []
        self.l = []
        self.other = []
        
        sl = ""

        for key,value in data.items():
            if "ContentObject" in str(type(value)): self.co.append((key,value))
            elif "list" in str(type(value)): self.l.append((key,value))
            else self.other.append((key,value))        


        



        for key,value in data.items():
            if ":" in key: key = key.split(":")[1]

            if "ContentObject" in str(type(value)):
                sl += "(%s %s )" % (key, toSL0(value))
            elif "list" in str(type(value)):
                sl += "(sequence "
                for i in value:
                    sl += "(%s %s)" % (key, toSL0(i))
                sl += ")"
            elif value != None and value != "None":
                sl += " :%s %s " % (key, value)


        return sl
    """
        
    def __str__(self):
        return co2xml(self)
        #return self.asRDFXML()


def Node2CO(node, nsdict):
    #print "NODE2CO: ",str(node)
    if len(node.kids) == 0:
        # Leaf node
        if node.getData():
            return node.getData()
        else:
            try:
                return node.attrs["rdf:resource"]
            except:
                return ""
    else:
        # Blank node
        s = ContentObject()
        for c in node.kids:
            #print "KID ",c.name," NS ",c.namespace
            if c.namespace in nsdict.keys():
                key = nsdict[c.namespace]+c.name
            else:
                key = c.name
            if not s.has_key(key):              
                s[key] = Node2CO(c,nsdict)
            else:
                # Possible list
                if "list" in str(type(s[key])):
                    # Append to the existing list
                    s[key].append(Node2CO(c,nsdict))
                else:
                    # Create a list with the current value and
                    # append the new one
                    s[key] = [s[key]]
                    s[key].append(Node2CO(c,nsdict))
        return s
            

def RDFXML2CO(rdfdata):
    #print "Gonna parse: "+rdfdata
    nb = simplexml.NodeBuilder(rdfdata)
    #print "Parsed: "+str(nb.getDom())+str(nb.namespaces)
    co = Node2CO(nb.getDom(), nb.namespaces)
    co.namespaces.update(nb.namespaces)
    return co


if __name__=="__main__":
    import urllib2
    #f = urllib2.urlopen("http://infomesh.net/2003/rdfparser/meta.rdf")
    #f = urllib2.urlopen("http://tourism.gti-ia.dsic.upv.es/rdf/ComidasTascaRapida.rdf")

    ex = """<rdf:RDF
      xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
      xmlns:foaf="http://xmlns.com/foaf/0.1/" 
      xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Description rdf:about="http://en.wikipedia.org/wiki/Tony_Benn">
            <dc:title>Tony Benn</dc:title>
            <dc:publisher>Wikipedia</dc:publisher>
            <foaf:primaryTopic>
                 <foaf:Person>
                      <foaf:name>Tony Benn</foaf:name>  
                 </foaf:Person>
            </foaf:primaryTopic>
        </rdf:Description>
    </rdf:RDF>
    """

    #sco = RDFXML2CO(f.read())
    sco = RDFXML2CO(ex)
    sco.addNamespace("http://spade.gti-ia-dsic.upv.es/ns/2.0/", "spade:")
    sco["rdf:Description"]["foaf:primaryTopic"]["spade:friend"] = []
    sco["rdf:Description"]["foaf:primaryTopic"]["spade:friend"].append("John Doe")
    sco["rdf:Description"]["foaf:primaryTopic"]["spade:friend"].append("Chuck Bartowski")
    sco["rdf:Description"]["foaf:primaryTopic"]["spade:friend"].append("Sarah Connor")
    sco["spade:uno"] = ContentObject()
    sco["spade:uno"]["spade:dos"] = "COSA"
    sco.uno["spade:tres"] = "OTRA"
    
    #print str(sco)
    print sco.pprint()
    #print sco["rdf:Description"]["dc:creator"]["foaf:name"], str(type(sco["rdf:Description"]["dc:creator"]["foaf:name"]))
    #print sco["rdf:Description"]["dc:creator"]["foaf:homePage"]
    print sco.asRDFXML()
    sco2 = RDFXML2CO(sco.asRDFXML())
    print sco2.pprint()
    print sco2.asRDFXML()
    
    #print sco2.asSL0()
