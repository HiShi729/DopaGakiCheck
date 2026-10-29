package jp.example.dopagaki;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Framework-free game rules. Questions and clip order change on each new session.
 * The numerical score is entertainment-only; it is not a validated assessment.
 */
public final class GameSession {
    public static final int CLIP_COUNT = 10;
    public static final int CONTENT_QUESTION_COUNT = 8;
    public static final int ORDER_QUESTION_COUNT = 2;
    public static final int QUIT_PENALTY_POINTS = 10;

    private static final ClipQuestion[][] CLIP_QUESTIONS = {
        {
            new ClipQuestion("時計の短い針は、どの数字の近くを指していた？", new String[]{"7", "8", "10", "11"}, 2, "時計は10時10分頃を示していました。"),
            new ClipQuestion("時計の長い針は、どの数字付近？", new String[]{"1", "2", "3", "4"}, 1, "時計の長針は2付近です。"),
            new ClipQuestion("時計が示していた時刻は？", new String[]{"10時10分ごろ", "10時30分ごろ", "7時10分ごろ", "12時10分ごろ"}, 0, "時計は約10時10分を指しています。")
        },
        {
            new ClipQuestion("机の上のマグカップは何色だった？", new String[]{"赤", "青", "白", "緑"}, 1, "マグカップの本体は青色でした。"),
            new ClipQuestion("マグカップが置かれていた場所は？", new String[]{"道路", "机の上", "ベッド", "棚の上"}, 1, "青いマグカップは机の上に置かれていました。"),
            new ClipQuestion("机の上にあった容器は？", new String[]{"皿", "水筒", "マグカップ", "花瓶"}, 2, "映っていたのはマグカップでした。")
        },
        {
            new ClipQuestion("植木鉢から伸びていた葉は何枚？", new String[]{"3枚", "4枚", "5枚", "6枚"}, 2, "左右に2枚ずつ、上に1枚で合計5枚でした。"),
            new ClipQuestion("植物が入っていたものは？", new String[]{"ガラス瓶", "植木鉢", "段ボール", "紙袋"}, 1, "植物は植木鉢に植えられていました。"),
            new ClipQuestion("植木鉢の動画で葉は上に何枚伸びていた？", new String[]{"0枚", "1枚", "2枚", "3枚"}, 1, "上に1枚の葉が伸びていました。")
        },
        {
            new ClipQuestion("本棚のいちばん右にあった本は何色？", new String[]{"赤", "黄", "青", "緑"}, 0, "右端の本は赤色でした。"),
            new ClipQuestion("本棚のいちばん右の本は何色？", new String[]{"赤", "黄", "青", "緑"}, 0, "右端の本は赤色でした。"),
            new ClipQuestion("本の並んでいた場所は？", new String[]{"階段", "本棚", "机", "床"}, 1, "本は本棚に並んでいました。")
        },
        {
            new ClipQuestion("バスの前面に表示されていた番号は？", new String[]{"3", "5", "7", "9"}, 2, "バス前面の行き先表示には7と書かれていました。"),
            new ClipQuestion("バスに表示された路線番号は？", new String[]{"3", "5", "7", "9"}, 2, "バスには7が表示されていました。"),
            new ClipQuestion("番号7が書かれていたのは？", new String[]{"電車", "バス", "自転車", "タクシー"}, 1, "番号7はバスの前面です。")
        },
        {
            new ClipQuestion("物干しにかかっていた服は何枚？", new String[]{"2枚", "3枚", "4枚", "5枚"}, 1, "白・黄・青の3枚の服がかかっていました。"),
            new ClipQuestion("物干しの服には何色があった？", new String[]{"白", "黒", "赤", "紫"}, 0, "白い服が掛かっていました。"),
            new ClipQuestion("服が掛かっていた場所は？", new String[]{"本棚", "物干し", "道路", "机"}, 1, "物干しに3枚の服が掛かっていました。")
        },
        {
            new ClipQuestion("ペン立てから出ていた鉛筆は何本？", new String[]{"2本", "3本", "4本", "5本"}, 1, "赤・黄・青緑の3本でした。"),
            new ClipQuestion("ペン立ての鉛筆は何本？", new String[]{"2本", "3本", "4本", "5本"}, 1, "鉛筆は3本でした。"),
            new ClipQuestion("鉛筆が入っていたものは？", new String[]{"ペン立て", "マグカップ", "引き出し", "筆箱"}, 0, "鉛筆はペン立てに入っていました。")
        },
        {
            new ClipQuestion("雨の日、歩く人の傘は何色？", new String[]{"青", "赤", "緑", "黄"}, 1, "傘は赤色でした。"),
            new ClipQuestion("雨の場面で使われていたのは？", new String[]{"帽子", "傘", "レインコート", "テント"}, 1, "歩く人が傘を使っていました。"),
            new ClipQuestion("赤かったものは？", new String[]{"傘", "靴", "帽子", "建物"}, 0, "赤かったのは傘でした。")
        },
        {
            new ClipQuestion("皿の上にあったトーストは何枚？", new String[]{"1枚", "2枚", "3枚", "4枚"}, 1, "重ねて置かれていたトーストは2枚でした。"),
            new ClipQuestion("トーストが載っていたのは？", new String[]{"皿", "フライパン", "まな板", "トレー"}, 0, "パンは皿に載っていました。"),
            new ClipQuestion("食べ物として映っていたのは？", new String[]{"ケーキ", "トースト", "クッキー", "おにぎり"}, 1, "トーストが2枚映っていました。")
        },
        {
            new ClipQuestion("カレンダーで赤い丸がついていた日付は？", new String[]{"11日", "12日", "14日", "17日"}, 2, "赤い丸で囲まれていたのは14日でした。"),
            new ClipQuestion("丸で囲まれていた日付は？", new String[]{"11日", "12日", "14日", "17日"}, 2, "丸で囲まれていたのは14日です。"),
            new ClipQuestion("14日に印をつけていたものは？", new String[]{"時計", "カレンダー", "地図", "ノート"}, 1, "カレンダーの14日に印がありました。")
        }
    };

    private static final class ClipQuestion {
        final String prompt;
        final String[] options;
        final int correctIndex;
        final String explanation;

        ClipQuestion(String prompt, String[] options, int correctIndex, String explanation) {
            this.prompt = prompt;
            this.options = options;
            this.correctIndex = correctIndex;
            this.explanation = explanation;
        }
    }

    public static final class QuizQuestion {
        public final int videoId;          // fixed ID for video assets (0..9)
        public final boolean isOrderQuestion;
        public final String prompt;
        public final String[] options;
        public final int correctIndex;
        public final String explanation;

        QuizQuestion(int videoId, boolean isOrderQuestion, String prompt,
                     String[] options, int correctIndex, String explanation) {
            this.videoId = videoId;
            this.isOrderQuestion = isOrderQuestion;
            this.prompt = prompt;
            this.options = options;
            this.correctIndex = correctIndex;
            this.explanation = explanation;
        }
    }

    public final int[] videoOrder = new int[CLIP_COUNT]; // playback slot -> clip asset ID
    public final QuizQuestion[] questions = new QuizQuestion[CLIP_COUNT];
    public final int[] answers = new int[CLIP_COUNT];
    public boolean finishedEarly = false;

    public GameSession() { this(new Random()); }

    /** Injected RNG allows deterministic test sessions. */
    public GameSession(Random random) {
        if (random == null) throw new IllegalArgumentException("random must not be null");
        Arrays.fill(answers, -1);
        for (int i = 0; i < CLIP_COUNT; i++) videoOrder[i] = i;
        shuffle(videoOrder, random);

        int[] positionByVideo = new int[CLIP_COUNT];
        for (int slot = 0; slot < CLIP_COUNT; slot++) {
            positionByVideo[videoOrder[slot]] = slot + 1;
        }

        // Exactly two distinct clips ask about playback order. All others ask about content.
        int[] quizTypeSelector = new int[CLIP_COUNT];
        for (int i = 0; i < CLIP_COUNT; i++) quizTypeSelector[i] = i;
        shuffle(quizTypeSelector, random);
        boolean[] askOrderForVideo = new boolean[CLIP_COUNT];
        for (int i = 0; i < ORDER_QUESTION_COUNT; i++) {
            askOrderForVideo[quizTypeSelector[i]] = true;
        }

        List<QuizQuestion> shuffledQuestions = new ArrayList<>(CLIP_COUNT);
        for (int videoId = 0; videoId < CLIP_COUNT; videoId++) {
            shuffledQuestions.add(askOrderForVideo[videoId]
                ? buildOrderQuestion(videoId, positionByVideo[videoId], random)
                : buildContentQuestion(videoId, random));
        }
        Collections.shuffle(shuffledQuestions, random);
        for (int i = 0; i < CLIP_COUNT; i++) questions[i] = shuffledQuestions.get(i);
    }

    private static QuizQuestion buildContentQuestion(int videoId, Random random) {
        ClipQuestion[] pool = CLIP_QUESTIONS[videoId];
        ClipQuestion base = pool[random.nextInt(pool.length)];
        // Option positions also vary so remembering the letter alone cannot help on replay.
        int[] optionOrder = {0, 1, 2, 3};
        shuffle(optionOrder, random);
        String[] options = new String[4];
        int correctIndex = -1;
        for (int i = 0; i < 4; i++) {
            options[i] = base.options[optionOrder[i]];
            if (optionOrder[i] == base.correctIndex) correctIndex = i;
        }
        return new QuizQuestion(videoId, false, base.prompt, options,
            correctIndex, base.explanation);
    }

    private static QuizQuestion buildOrderQuestion(int videoId, int correctPosition, Random random) {
        List<Integer> positions = new ArrayList<>(CLIP_COUNT);
        for (int i = 1; i <= CLIP_COUNT; i++) {
            if (i != correctPosition) positions.add(i);
        }
        Collections.shuffle(positions, random);
        List<Integer> optionsAsNumbers = new ArrayList<>(4);
        optionsAsNumbers.add(correctPosition);
        for (int i = 0; i < 3; i++) optionsAsNumbers.add(positions.get(i));
        Collections.shuffle(optionsAsNumbers, random);
        String[] options = new String[4];
        int correctIndex = -1;
        for (int i = 0; i < 4; i++) {
            int position = optionsAsNumbers.get(i);
            options[i] = position + "番目";
            if (position == correctPosition) correctIndex = i;
        }
        String explanation = "この動画は、今回の再生順で" + correctPosition + "番目に流れました。";
        return new QuizQuestion(videoId, true,
            "この動画は、何番目に流れましたか？", options, correctIndex, explanation);
    }

    private static void shuffle(int[] items, Random random) {
        for (int i = items.length - 1; i > 0; i--) {
            int swapWith = random.nextInt(i + 1);
            int temp = items[i];
            items[i] = items[swapWith];
            items[swapWith] = temp;
        }
    }

    public void submitAnswer(int questionIndex, int chosenIndex) {
        if (finishedEarly) throw new IllegalStateException("The quiz has ended");
        if (questionIndex < 0 || questionIndex >= questions.length) {
            throw new IllegalArgumentException("Invalid question index");
        }
        if (answers[questionIndex] != -1) throw new IllegalStateException("Already answered");
        if (chosenIndex < 0 || chosenIndex >= questions[questionIndex].options.length) {
            throw new IllegalArgumentException("Invalid option index");
        }
        answers[questionIndex] = chosenIndex;
    }

    public void quitQuiz() {
        if (answeredCount() == CLIP_COUNT) throw new IllegalStateException("Quiz completed");
        finishedEarly = true;
    }

    public int answeredCount() {
        int sum = 0;
        for (int answer : answers) if (answer >= 0) sum++;
        return sum;
    }

    public int correctCount() {
        int sum = 0;
        for (int i = 0; i < CLIP_COUNT; i++) {
            if (answers[i] >= 0 && answers[i] == questions[i].correctIndex) sum++;
        }
        return sum;
    }

    /** Scaled over all 10 questions; unanswered questions count as incorrect. */
    public int overallAccuracyPercent() { return (100 * correctCount()) / CLIP_COUNT; }

    /** An extra 10 points is applied when the user voluntarily ends the quiz early. */
    public int dopaScorePercent() {
        int rawScore = 100 - overallAccuracyPercent() + (finishedEarly ? QUIT_PENALTY_POINTS : 0);
        return Math.min(100, rawScore);
    }
}
