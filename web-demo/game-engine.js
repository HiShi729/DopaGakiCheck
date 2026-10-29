'use strict';
/* Browser rules mirror GameSession.java. Source questions: stories.js. */
(function(root) {
 const CLIP_COUNT=10;
 const STORIES=(typeof module!=='undefined' && module.exports) ? require('./stories.js') : root.DopaStories;
 if(!Array.isArray(STORIES)||STORIES.length<CLIP_COUNT)throw new Error('Story bank missing');
 const CONTENT=STORIES.map(s=>s.questions);
 function shuffle(a,rng=Math.random){for(let i=a.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
 function buildQuestion(videoId){
   const bank=CONTENT[videoId];
   const q=bank[Math.floor(Math.random()*bank.length)];
   const order=shuffle([0,1,2,3]);
   return {videoId,prompt:q.prompt,options:order.map(i=>q.options[i]),
           correctIndex:order.indexOf(q.correctIndex),explanation:q.explanation};
 }
 function createSession(){
   const videoOrder=shuffle(Array.from({length:STORIES.length},(_,i)=>i)).slice(0,CLIP_COUNT);
   const questions=shuffle(videoOrder.map(buildQuestion));
   return {videoOrder,questions,answers:Array(CLIP_COUNT).fill(-1),finishedEarly:false};
 }
 function submitAnswer(s,index,choice){
   if(s.finishedEarly||index<0||index>=CLIP_COUNT||s.answers[index]!==-1||choice<0||choice>3)
     throw new Error('Invalid answer');
   s.answers[index]=choice;
 }
 function quitQuiz(s){if(s.answers.every(v=>v>=0))throw new Error('Quiz completed');s.finishedEarly=true;}
 function answeredCount(s){return s.answers.filter(v=>v>=0).length;}
 function correctCount(s){return s.answers.filter((v,i)=>v>=0&&v===s.questions[i].correctIndex).length;}
 function overallAccuracyPercent(s){return correctCount(s)*10;}
 function dopaScorePercent(s){return Math.min(100,100-overallAccuracyPercent(s)+(s.finishedEarly?10:0));}
 const api={STORIES,CONTENT,createSession,submitAnswer,quitQuiz,answeredCount,correctCount,overallAccuracyPercent,dopaScorePercent};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 if(root)root.DopaGakiGame=api;
})(typeof window!=='undefined'?window:null);
