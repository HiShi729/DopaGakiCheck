"use strict";
/* Shared browser game rules. Native GameSession.java implements equivalent rules. */
(function (root) {
  const CLIP_COUNT = 10;
  const CONTENT = [
    {
      prompt: "時計の短い針は、どの数字の近くを指していた？",
      options: ["7", "8", "10", "11"],
      correctIndex: 2,
      explanation: "時計は10時10分頃を示していました。",
    },
    {
      prompt: "机の上のマグカップは何色だった？",
      options: ["赤", "青", "白", "緑"],
      correctIndex: 1,
      explanation: "マグカップの本体は青色でした。",
    },
    {
      prompt: "植木鉢から伸びていた葉は何枚？",
      options: ["3枚", "4枚", "5枚", "6枚"],
      correctIndex: 2,
      explanation: "左右に2枚ずつ、上に1枚で合計5枚でした。",
    },
    {
      prompt: "本棚のいちばん右にあった本は何色？",
      options: ["赤", "黄", "青", "緑"],
      correctIndex: 0,
      explanation: "右端の本は赤色でした。",
    },
    {
      prompt: "バスの前面に表示されていた番号は？",
      options: ["3", "5", "7", "9"],
      correctIndex: 2,
      explanation: "バス前面の行き先表示には7と書かれていました。",
    },
    {
      prompt: "物干しにかかっていた服は何枚？",
      options: ["2枚", "3枚", "4枚", "5枚"],
      correctIndex: 1,
      explanation: "白・黄・青の3枚の服がかかっていました。",
    },
    {
      prompt: "ペン立てから出ていた鉛筆は何本？",
      options: ["2本", "3本", "4本", "5本"],
      correctIndex: 1,
      explanation: "赤・黄・青緑の3本でした。",
    },
    {
      prompt: "雨の日、歩く人の傘は何色？",
      options: ["青", "赤", "緑", "黄"],
      correctIndex: 1,
      explanation: "傘は赤色でした。",
    },
    {
      prompt: "皿の上にあったトーストは何枚？",
      options: ["1枚", "2枚", "3枚", "4枚"],
      correctIndex: 1,
      explanation: "重ねて置かれていたトーストは2枚でした。",
    },
    {
      prompt: "カレンダーで赤い丸がついていた日付は？",
      options: ["11日", "12日", "14日", "17日"],
      correctIndex: 2,
      explanation: "赤い丸で囲まれていたのは14日でした。",
    },
  ];
  function shuffle(list, rng) {
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
    return list;
  }
  function createSession(rng = Math.random) {
    const videoOrder = shuffle(
      Array.from({ length: CLIP_COUNT }, (_, i) => i),
      rng,
    );
    const positionByVideo = Array(CLIP_COUNT).fill(0);
    videoOrder.forEach((videoId, slot) => {
      positionByVideo[videoId] = slot + 1;
    });
    const selectedOrderIds = shuffle(
      Array.from({ length: CLIP_COUNT }, (_, i) => i),
      rng,
    ).slice(0, 2);
    const questions = [];
    for (let videoId = 0; videoId < CLIP_COUNT; videoId++) {
      if (selectedOrderIds.includes(videoId)) {
        const correctPosition = positionByVideo[videoId];
        const alternatives = shuffle(
          Array.from({ length: CLIP_COUNT }, (_, i) => i + 1).filter(
            (p) => p !== correctPosition,
          ),
          rng,
        );
        const nums = shuffle(
          [correctPosition, ...alternatives.slice(0, 3)],
          rng,
        );
        questions.push({
          videoId,
          isOrderQuestion: true,
          prompt: "この動画は、何番目に流れましたか？",
          options: nums.map((p) => p + "番目"),
          correctIndex: nums.indexOf(correctPosition),
          explanation:
            "この動画は、今回の再生順で" +
            correctPosition +
            "番目に流れました。",
        });
      } else {
        const base = CONTENT[videoId];
        const indices = shuffle([0, 1, 2, 3], rng);
        questions.push({
          videoId,
          isOrderQuestion: false,
          prompt: base.prompt,
          options: indices.map((i) => base.options[i]),
          correctIndex: indices.indexOf(base.correctIndex),
          explanation: base.explanation,
        });
      }
    }
    shuffle(questions, rng);
    return {
      videoOrder,
      questions,
      answers: Array(CLIP_COUNT).fill(-1),
      finishedEarly: false,
    };
  }
  function submitAnswer(session, questionIndex, optionIndex) {
    if (session.finishedEarly) throw new Error("Quiz already finished");
    const q = session.questions[questionIndex];
    if (
      !q ||
      session.answers[questionIndex] !== -1 ||
      !Number.isInteger(optionIndex) ||
      optionIndex < 0 ||
      optionIndex >= q.options.length
    )
      throw new Error("Invalid answer");
    session.answers[questionIndex] = optionIndex;
  }
  function quitQuiz(session) {
    if (answeredCount(session) === CLIP_COUNT)
      throw new Error("Already complete");
    session.finishedEarly = true;
  }
  function answeredCount(session) {
    return session.answers.filter((a) => a >= 0).length;
  }
  function correctCount(session) {
    return session.answers.filter(
      (a, i) => a >= 0 && a === session.questions[i].correctIndex,
    ).length;
  }
  function overallAccuracyPercent(session) {
    return correctCount(session) * 10;
  }
  function dopaScorePercent(session) {
    return Math.min(
      100,
      100 - overallAccuracyPercent(session) + (session.finishedEarly ? 10 : 0),
    );
  }
  const api = {
    CLIP_COUNT,
    CONTENT,
    createSession,
    submitAnswer,
    quitQuiz,
    answeredCount,
    correctCount,
    overallAccuracyPercent,
    dopaScorePercent,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.DopaGakiGame = api;
})(typeof window === "undefined" ? null : window);
