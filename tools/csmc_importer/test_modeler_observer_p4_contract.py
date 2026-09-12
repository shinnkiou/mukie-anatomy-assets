from pathlib import Path

p = Path(__file__).with_name('modeler_observer').joinpath('BP3D_ModelerObserver_P4.ps1')
text = p.read_text(encoding='utf-8')
required = [
    'MEM_PRIVATE=0x20000',
    'if(type!=MEM_PRIVATE||magic<4)return null;',
    'if(kind!="character")return null;',
    'if(ver!=2||logical<1024||stored<1024||stored>1073741824U||stored<logical)return null;',
    'bool invariant=relation==8;',
    'if(!invariant)return null;',
    'if($last.Count-ne1)',
    'automatic_network_upload=$false',
    "Write-Host 'Keep the runtime .bin/ZIP private; do not publish it to GitHub.'",
]
for needle in required:
    assert needle in text, needle
for forbidden in ['WriteProcessMemory', 'VirtualProtectEx', 'CreateRemoteThread', 'Invoke-WebRequest', 'Invoke-RestMethod']:
    assert forbidden not in text, forbidden
print('Modeler Observer P4 static contract: PASS')
