# using virtualenv ICE  
# to use source ICE/bin/activate
#
# This is a python3 project.
#
# use a combination of py2neo: low level python calls to graph and cypher
"""
use artoo to scrape the page:
// var aList = artoo.scrapeTable(
//  '#node-most-wanted-33362 > div.content.clearfix > div > div.most-wanted-text > div.clearfix')
// artoo.savePrettyJson(aList)

hand massage each scraped item and concat onto the main data file (badguys0.json)

Example Queries

match (you:Person {Name: 'Hernandez__Ingrid_Estela'})
CREATE (you)-[born:BORN]->(elSalvador:Place {name: 'El Salvador'})
return you,born,elSalvador

match (you:Person {Name: 'Yunusov__Nodir'})
CREATE (you)-[citizen:CITIZEN]->(uzbekistan:Place {name: 'Uzbekistan'})
return you, Uzbekistan

match (you:Person {Name: "$name"})
CREATE (you)-[placeofbirth:PLACEOFBIRTH]-($nameLower:Place {name: "$name"})
return you, $nameLower


match (n1)-[:BORN]-(p:Place {name: "El Salvador"}) return n1, p

"""

import json
from py2neo import Graph, Node, Relationship
import re 
from string import Template

def cleanWanted(wanted):
  """
  remove '()' from wanted
  """
  p = re.sub(r'\(', '', wanted)
  p = re.sub(r'\)', '', p)
  p = re.sub(r' ', '_', p)
  p = re.sub(r'-', '_', p)
  p = re.sub(r',', '', p)
  p = re.sub(r'\.', '', p)
  return p

def strip2End(place):
  """
  find the last ','
  return from the ',' to the end
  """
  i = place.rfind(',')
  if i == -1:
    return place
  p = place[i+2:]
  
  return p

def convertPlace(place):
  """
  change ' ' to _
  """
  p = re.sub(r' ', '_', place)
  p = re.sub(r',', '', p)
  return p

def convertName(name):
  """ 
  change the ',' to '_'
  change the '-' to ''
  change the spaces to '_'
  """
  nm = re.sub(r',', '_', name)
  nm = re.sub(r'-', '', nm)
  nm = re.sub(r'\s', "_", nm)

  return nm

with open("badguys0.json", 'r') as fi:
  data = fi.read()
fi.close

js = json.loads(data)

# print(type(js))
lst = list(js.keys())
print(len(lst))
# print(js[lst[2]])

graph = Graph(host='localhost', port=7687, auth=('neo4j', 'newpass'))
graph.delete_all()
for i,p in enumerate(js):
  # print( p, js[p]['Name'])
  nm = convertName(js[p]['Name'])
  

  fst = "CREATE ( " +  nm + ":Person { Name: \"" + nm + "\" } )"
  # fst= "CREATE ( \"" + js[p]['Name'] + "\":Person"
  # prop = "{ Name: \"" + js[p]['Name'] + "\"})"
  stt = fst
  # print(stt)
  graph.evaluate(stt)


for i,p in enumerate(js):
  if 'Place of Birth' in js[p].keys():
    pob = js[p]['Place of Birth']
    if pob == "N/A":
      continue
    pobLast = strip2End(pob)
    # print(pobLast)
    
    pobLower=convertPlace(pob)
    nm = convertName(js[p]['Name'])
    query = """
      match (you:Person {Name: "$name"})
      CREATE (you)-[born:BORN]->($placeLower:Place {name: "$place"})
      return you, $placeLower
    """
    s = Template(query)
    fst = s.substitute(name=nm, placeLower=(pobLower.lower()), place=pobLast)
    # print(fst)
    graph.run(fst)

j = 0
for i, p in enumerate(js):
  if 'Wanted For' in js[p].keys():
    wf = js[p]['Wanted For']
    wf = cleanWanted(wf)
    # print(wf)
    if wf == "N/A":
      continue
    nm = convertName(js[p]['Name'])
    query = """
      MATCH (you:Person {Name: "$name"})
      CREATE (you)-[wanted:WANTEDFOR]->($wantedforLower:Wanted {name: "$wantedFor"})
      RETURN you, $wantedforLower
    """
    s = Template(query)
    fst = s.substitute(name=nm, wantedforLower=(wf.lower()), wantedFor=wf)
    print(fst)
    graph.run(fst)
    j += 1
print(j)

j = 0
for i,p in enumerate(js):
  if 'details' in js[p].keys():
    details = js[p]['details']
    nm = convertName(js[p]['Name'])
    f = re.search(r'gang|MS\s*-13', details)  
    if f is not None:
      query = """
        MATCH (you:Person {Name: "$name"})
        CREATE (you)-[member:MEMBEROF]->($gangLower:Member {name: "$gmem"})
        RETURN you, $gangLower
      """
      s = Template(query)
      fst = s.substitute(name=nm, gangLower='gang', gmem=f.group())
      print(fst)
      graph.run(fst)
      j += 1
print(j)