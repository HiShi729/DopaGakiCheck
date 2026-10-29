'use strict';
const assert=require('node:assert/strict');
const Game=require('../web-demo/game-engine.js');
const bases=Game.CONTENT;
let permutations=new Set();
for (let trial=0; trial<1200; trial++) {
 const s=Game.createSession();
 permutations.add(s.videoOrder.join(','));
 assert.equal(new Set(s.videoOrder).size,10);
 assert.equal(s.questions.length,10);
 assert.equal(s.questions.filter(q=>q.isOrderQuestion).length,2);
 assert.equal(s.questions.filter(q=>!q.isOrderQuestion).length,8);
 assert.equal(new Set(s.questions.map(q=>q.videoId)).size,10);
 const pos=Object.fromEntries(s.videoOrder.map((v,i)=>[v,i+1]));
 for (let i=0;i<10;i++) {
  const q=s.questions[i];
  assert.equal(new Set(q.options).size,4);
  if(q.isOrderQuestion) {
   assert.equal(q.options[q.correctIndex],pos[q.videoId]+'番目');
  } else {
   assert.ok(bases[q.videoId].some(base=>q.options[q.correctIndex]===base.options[base.correctIndex] && q.prompt===base.prompt));
  }
 }
 for(let i=0;i<10;i++) Game.submitAnswer(s,i,s.questions[i].correctIndex);
 assert.equal(Game.correctCount(s),10);
 assert.equal(Game.dopaScorePercent(s),0);
}
assert.ok(permutations.size>1100);
const s=Game.createSession();
for(let i=0;i<3;i++) Game.submitAnswer(s,i,s.questions[i].correctIndex);
Game.quitQuiz(s);
assert.equal(Game.answeredCount(s),3);
assert.equal(Game.overallAccuracyPercent(s),30);
assert.equal(Game.dopaScorePercent(s),80);
assert.throws(()=>Game.submitAnswer(s,3,0));
const empty=Game.createSession();Game.quitQuiz(empty);
assert.equal(Game.dopaScorePercent(empty),100);
console.log('JS game engine: 1200 sessions, 8+2 questions, shuffle, order choices, perfect score, quit penalty PASSED');
