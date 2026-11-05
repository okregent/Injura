import shutil
import subprocess
from pathlib import Path

import pytest


def test_preview_renders_untrusted_text_and_invalidates_stale_selection(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is needed to verify preview browser logic')
    page = (Path(__file__).parents[1] / 'apps/api/index.html').read_text(encoding='utf-8')
    script = page.split('<script>')[1].split('</script>')[0]
    harness = '''
const assert=require('assert'),elements={};
global.document={getElementById(id){return elements[id] ||= {value:'',hidden:true,disabled:false,textContent:'',children:[],
 replaceChildren(){this.children=[]},append(item){this.children.push(item)}};},createElement(){return {textContent:''}}};
global.fetch=()=>new Promise(()=>{});
'''
    assertions = '''
const payload={overview:{state:'capture_review',primary_action:'<script>alert(1)</script>',detected_cycles:3,
 excluded_candidates:1,personal_comparison_state:'not_requested',accuracy_status:'not_validated',coaching_status:'pending_validation'},
 feedback:{actions:[{action:'<img src=x>',repetitions:[1]}],notices:[],cards:[]}};
showResult(payload);assert.strictEqual(el('summary').textContent,'capture_review · <script>alert(1)</script>');
assert.strictEqual(el('actions').children[0].textContent,'<img src=x> · Repetitions 1');
assert.strictEqual(result,payload);el('side').onchange();assert.strictEqual(result,null);assert.strictEqual(el('result').hidden,true);
setBusy(true);assert.strictEqual(el('video').disabled,true);assert.strictEqual(el('side').disabled,true);
setBusy(false);assert.strictEqual(el('submit').disabled,false);
'''
    path = tmp_path / 'preview.cjs'
    path.write_text(harness + script + assertions, encoding='utf-8')
    result = subprocess.run([node, str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'innerHTML' not in script
