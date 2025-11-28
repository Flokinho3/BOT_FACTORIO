import os

# Deine o diretorio atual
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FACTORY_DIR1 = os.path.join(CURRENT_DIR, '../../factorio-server/')
FACTORY_DIR = os.path.abspath(os.path.join(FACTORY_DIR1, 'factorio-2.0/'))
FACTORY_MODS_FILE = os.path.join(FACTORY_DIR, 'mods/')
FACTORY_COMMANDS_FILE = os.path.join(FACTORY_DIR, 'commands.txt')
FACTORY_SCRIPT_OUTPUT_DIR = os.path.join(FACTORY_DIR, 'script-output/')
FACTORY_SCRIPT_OUTPUT_FILE = os.path.join(FACTORY_SCRIPT_OUTPUT_DIR, 'resposta.json')

