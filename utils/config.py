""" Configuration constants """

######### NILE ########

NILE_OPERATIONS = ['add', 'remove', 'from', 'to', 'set', 'unset', 'allow', 'block', 'start', 'end', 'for']
NILE_ACTIONS_NEGATION = {
    "add": "remove",
    "allow": "block",
    "set": "unset"
}

######### DEPLOYMENT ########

OPENFLOW_RULES_PATH = "../res/openflow_rules.json"
TC_COMMANDS_PATH = "../res/tc_rules.json"

MERLIN_WORKKING_PATH = "/home/heitor/mininet/merlin/"
MERLIN_EXEC = "merlinAgent-Linux-x64"
MERLIN_FILE_OUTPUT = "generated_merlin.mln"
MERLIN_EXEC_OUTPUT = "../res/merlin_output.txt"


########## PATH ###########
MODEL_WEIGHTS_PATH = "../res/weights/{}_{}.joblib"

TOPOLOGY_PATH = "../res/topology.json"
TOPOLOGY_DOT_PATH = "../res/topology.dot"
LEARNING_CURVE_PATH = "../res/results/learning_curve_{}_{}.csv"

COMPILATION_DATASET_PATH = "../res/dataset/compilation.json"
COMPILATION_RESULTS_PATH = "../res/dataset/compilation.csv"

EXTRACTION_DATASET_PATH = "../res/dataset/extraction_{}.json"
EXTRACTION_RESULTS_PATH = "../res/results/extraction_{}.csv"

CONTRADICTIONS_DATASET_PATH = "../res/dataset/contradictions_{}.json"
CONTRADICTIONS_RESULTS_PATH = "../res/results/contradictions_{}_{}.csv"


########## DATASET ##########

DATASET_SIZES = [100, 500, 1000, 2500, 5000, 10000]
DATASET_ACTIONS_MBS = ['add', 'remove']
DATASET_ACTIONS_ACL = ['allow', 'block']
DATASET_ACTIONS_QOS = ['set', 'unset']
DATASET_GROUPS = ['students', 'staff', 'professors', 'dorms']
DATASET_MIDDLEBOXES = ['firewall', 'dpi', 'ids', 'load-balancer', 'parental-control']
DATASET_SERVICES = ['netflix', 'youtube', 'facebook', 'vimeo', 'amazon-prime', 'instagram', 'popcorn-time', 'stremio', 'bittorrent']
DATASET_TRAFFIC = ['peer2peer', 'torrent', 'streaming', 'social-media']
DATASET_PROTOCOLS = ['udp', 'tcp', 'https', 'http', 'smtp', 'icmp', 'telnet', 'snmp', 'sftp', 'ftp', 'quic']
DATASET_QOS_METRICS = [('bandwidth', 'mbps'), ('quota', 'gb/wk')]
DATASET_QOS_CONSTRAINTS = ['min', 'max']

DATASET_SERVICE_ASSOCIATIONS = {
    "netflix": {
        "protocol": ['tcp', 'https'],
        "traffic": ['streaming']
    },
    "youtube": {
        "protocol": ['udp', 'https', 'quic'],
        "traffic": ['streaming']
    },
    "facebook": {
        "protocol": ['tcp', 'https'],
        "traffic": ['streaming', 'social-media']
    },
    "instagram": {
        "protocol": ['tcp', 'https'],
        "traffic": ['social-media']
    },
    "vimeo": {
        "protocol": ['tcp', 'https'],
        "traffic": ['streaming']
    },
    "amazon-prime": {
        "protocol": ['tcp', 'https'],
        "traffic": ['streaming']
    },
    'popcorn-time': {
        "protocol": ['udp'],
        "traffic": ['peer2peer', 'torrent']
    },
    'stremio': {
        "protocol": ['udp'],
        "traffic": ['peer2peer', 'torrent']
    },
    'bittorrent': {
        "protocol": ['udp'],
        "traffic": ['peer2peer', 'torrent']
    }
}

DATASET_TRAFFIC_ASSOCIATIONS = {
    "streaming": {
        "protocol": ['tcp', 'https', 'quic', 'udp'],
        "service": ['netflix', 'youtube', 'vimeo', 'amazon-prime', 'facebook']
    },
    "social-media": {
        "protocol": ['tcp', 'https'],
        "service": ['facebook', 'instagram']
    },
    "peer2peer": {
        "protocol": ['udp'],
        "service": ['bittorrent', 'utorrent', 'stremio', 'popcorn-time']
    },
    "torrent": {
        "protocol": ['udp'],
        "service": ['bittorrent', 'utorrent', 'stremio', 'popcorn-time']
    }
}

DATASET_SYNONYMS = {
    "dorms": ["dormitory", "hall", "dorm", "residence_hall", "student_residence"],
    "professors": ["professor", "prof"],
    "staff": ["faculty"],
    "students": ["student", "pupil", "educatee", "scholar", "scholarly_person", "bookman"]
}
