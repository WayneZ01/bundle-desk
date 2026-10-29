const vm=require('node:vm');const fs=require('node:fs');const assert=require('node:assert/strict');
async function scenario(failFirst=false){
 const elements={};const element=id=>elements[id]??=( {id,files:[],value:'',options:[],textContent:'',disabled:false,append(){},replaceChildren(){this.options=[]},add(o){this.options.push(o)}} );
 const calls=[];let attempts=0;
 const ctx=vm.createContext({document:{getElementById:element,createElement:()=>({})},location:{hash:'#test-token',pathname:'/'},history:{replaceState(){}},sessionStorage:{getItem(){return null},setItem(){}},Option:function(text,value){return {text,value}},setTimeout,URL,Blob,fetch:async(path,options={})=>{
  if(path==='/api/status')return {ok:true,json:async()=>({environment:{},devices:[]})};
  if(path==='/api/upload'){
   attempts++;if(failFirst&&attempts===1)return {ok:false,json:async()=>({error:'模拟导入失败'})};
   assert(options.body instanceof ArrayBuffer);return {ok:true,json:async()=>({id:'aab-token',name:'test.aab'})};
  }
  if(path==='/api/jobs'){calls.push(JSON.parse(options.body));return {ok:true,json:async()=>({state:'done',result:{},logs:[]})}}
  throw Error(path);
 }});
 vm.runInContext(fs.readFileSync('app/web/app.js','utf8'),ctx);
 element('aab').files=[{name:'test.aab',arrayBuffer:async()=>new ArrayBuffer(4)}];
 await vm.runInContext("upload($('aab'))",ctx);
 if(failFirst)assert.match(element('uploadStatus').textContent,/导入失败/);
 await vm.runInContext("job('build')",ctx);
 assert.equal(calls.length,1);assert.equal(calls[0].aab,'aab-token');assert.equal(calls[0].keystore,undefined);
 assert.equal(attempts,failFirst?2:1);
 await vm.runInContext("job('inspect')",ctx);assert.equal(calls[1].action,'inspect');
}
(async()=>{await scenario();await scenario(true);console.log('PASS: AAB only build/inspect; failed upload retry; exact uploaded file ID; no keystore required')})().catch(e=>{console.error(e);process.exitCode=1});
