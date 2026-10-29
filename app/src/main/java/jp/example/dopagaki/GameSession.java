package jp.example.dopagaki;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/** A ten-story comprehension quiz drawn without repetition from twenty clips.
 * Pure Java and deterministic when supplied a seeded Random for testing.
 * The score is for entertainment and does not diagnose any health condition.
 */
public final class GameSession {
    public static final int CLIP_COUNT = 10;
    public static final int VIDEO_POOL_COUNT = StoryData.POOL_COUNT;
    public static final int CONTENT_QUESTION_COUNT = CLIP_COUNT;
    public static final int QUIT_PENALTY_POINTS = 10;

    static final class ClipQuestion {
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
        public final int videoId; // index into the 20 story clips
        public final String prompt;
        public final String[] options;
        public final int correctIndex;
        public final String explanation;
        QuizQuestion(int videoId, String prompt, String[] options, int correctIndex,
                     String explanation) {
            this.videoId = videoId;
            this.prompt = prompt;
            this.options = options;
            this.correctIndex = correctIndex;
            this.explanation = explanation;
        }
    }

    public final int[] videoOrder = new int[CLIP_COUNT];
    public final QuizQuestion[] questions = new QuizQuestion[CLIP_COUNT];
    public final int[] answers = new int[CLIP_COUNT];
    public boolean finishedEarly = false;

    public GameSession() { this(new Random()); }

    public GameSession(Random random) {
        if (random == null) throw new IllegalArgumentException("random must not be null");
        if (VIDEO_POOL_COUNT < CLIP_COUNT || StoryData.QUESTION_BANK.length != VIDEO_POOL_COUNT)
            throw new IllegalStateException("Invalid story bank");
        Arrays.fill(answers, -1);
        int[] candidates = new int[VIDEO_POOL_COUNT];
        for (int i = 0; i < candidates.length; i++) candidates[i] = i;
        shuffle(candidates, random);
        System.arraycopy(candidates, 0, videoOrder, 0, CLIP_COUNT);

        List<QuizQuestion> ordered = new ArrayList<>(CLIP_COUNT);
        for (int videoId : videoOrder) ordered.add(buildQuestion(videoId, random));
        Collections.shuffle(ordered, random);
        for (int i = 0; i < CLIP_COUNT; i++) questions[i] = ordered.get(i);
    }

    private static QuizQuestion buildQuestion(int videoId, Random random) {
        ClipQuestion[] bank = StoryData.QUESTION_BANK[videoId];
        if (bank == null || bank.length == 0) throw new IllegalStateException("Missing story questions");
        ClipQuestion base = bank[random.nextInt(bank.length)];
        if (base.options.length != 4) throw new IllegalStateException("Each question needs four options");
        int[] order = {0, 1, 2, 3};
        shuffle(order, random);
        String[] options = new String[4];
        int correctIndex = -1;
        for (int i = 0; i < 4; i++) {
            options[i] = base.options[order[i]];
            if (order[i] == base.correctIndex) correctIndex = i;
        }
        return new QuizQuestion(videoId, base.prompt, options, correctIndex, base.explanation);
    }

    private static void shuffle(int[] items, Random random) {
        for (int i = items.length - 1; i > 0; i--) {
            int j = random.nextInt(i + 1);
            int t = items[i]; items[i] = items[j]; items[j] = t;
        }
    }

    public void submitAnswer(int index, int option) {
        if (finishedEarly) throw new IllegalStateException("Quiz already ended");
        if (index < 0 || index >= CLIP_COUNT) throw new IllegalArgumentException("Invalid question index");
        if (answers[index] != -1) throw new IllegalStateException("Question already answered");
        if (option < 0 || option >= questions[index].options.length)
            throw new IllegalArgumentException("Invalid answer index");
        answers[index] = option;
    }

    public void quitQuiz() {
        if (answeredCount() == CLIP_COUNT) throw new IllegalStateException("Quiz completed");
        finishedEarly = true;
    }

    public int answeredCount() {
        int n = 0;
        for (int answer : answers) if (answer >= 0) n++;
        return n;
    }

    public int correctCount() {
        int n = 0;
        for (int i = 0; i < CLIP_COUNT; i++)
            if (answers[i] >= 0 && answers[i] == questions[i].correctIndex) n++;
        return n;
    }

    public int overallAccuracyPercent() { return 100 * correctCount() / CLIP_COUNT; }

    public int dopaScorePercent() {
        return Math.min(100, 100 - overallAccuracyPercent()
            + (finishedEarly ? QUIT_PENALTY_POINTS : 0));
    }
}
