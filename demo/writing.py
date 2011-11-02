import datetime
from configman import Namespace, ConfigurationManager

def start():
    n = Namespace()
    n.add_option('name')
    n.add_option('age', doc="Age in years")
    n.add_option('password')
    n.add_option('bday', default=datetime.date(1979, 12, 13))

    config = ConfigurationManager([n])
    print "CONF (WITH COMMENTS)"
    with file('sample.conf', 'w') as f:
        config.write_conf(f)

#    print '-'*80
    with file('sample.ini', 'w') as f:
        config.write_ini(f)
#    print '-'*80
#    config.write_json()

    #config = ConfigurationManager([n])
    #print "CONF (WITHOUT COMMENTS)"
    #config.write_conf(comments=False)




if __name__ == '__main__':
    start()
