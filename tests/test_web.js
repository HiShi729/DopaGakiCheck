'use strict';
const assert=require('node:assert/strict');
const Game=require('../web-demo/game-engine.js');
assert.equal(Game.STORIES.length,20);
assert.equal(Game.CONTENT.reduce((a,b)=>a+b.length,0),60);
let sampleSets=new Set();
const hits=Array(20).fill(0);
for(let trial=0;trial<2000;trial++){
 const s=Game.createSession();
 assert.equal(s.videoOrder.length,10);
 assert.equal(new Set(s.videoOrder).size,10);
 assert.equal(s.questions.length,10);
 assert.equal(new Set(s.questions.map(q=>q.videoId)).size,10);
 sampleSets.add([...s.videoOrder].sort((a,b)=>a-b).join(','));
 for(const q of s.questions){
   assert.ok(s.videoOrder.includes(q.videoId));
   assert.equal(new Set(q.options).size,4);
   assert.ok(!q.isOrderQuestion);
   assert.doesNotMatch(q.prompt,/何色|何枚|何本|何番目|何個/);
   const base=Game.CONTENT[q.videoId].find(x=>x.prompt===q.prompt);
   assert.ok(base,'quiz must originate in corresponding story bank');
   assert.equal(q.options[q.correctIndex],base.options[base.correctIndex]);
   hits[q.videoId]++;
 }
 for(let i=0;i<10;i++)Game.submitAnswer(s,i,s.questions[i].correctIndex);
 assert.equal(Game.correctCount(s),10);
 assert.equal(Game.dopaScorePercent(s),0);
}
assert.ok(sampleSets.size>1000);
assert.ok(hits.every(n=>n>100));
const s=Game.createSession();
for(let i=0;i<3;i++)Game.submitAnswer(s,i,s.questions[i].correctIndex);
Game.quitQuiz(s);
assert.equal(Game.answeredCount(s),3);
assert.equal(Game.dopaScorePercent(s),80);
assert.throws(()=>Game.submitAnswer(s,3,0));
console.log('JS: 2000 sessions, 20 silent story clips, 60 questions, no order trivia PASS');
