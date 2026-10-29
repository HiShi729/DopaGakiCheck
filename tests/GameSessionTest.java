import jp.example.dopagaki.GameSession;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Random;
import java.util.Set;

/** Run with: sh tests/run_tests.sh (no Android SDK needed). */
public final class GameSessionTest {
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        Set<String> permutations = new HashSet<>();
        for (int seed=0; seed < 1200; seed++) {
            GameSession game = new GameSession(new Random(seed));
            permutations.add(Arrays.toString(game.videoOrder));
            boolean[] seen = new boolean[10];
            int[] positions = new int[10];
            for (int i=0; i<10; i++) {
                int videoId = game.videoOrder[i];
                require(videoId>=0 && videoId<10 && !seen[videoId], "video ID repeats");
                seen[videoId] = true;
                positions[videoId] = i+1;
            }
            int orderQuestions=0, contentQuestions=0;
            boolean[] askedVideos = new boolean[10];
            for (GameSession.QuizQuestion q:game.questions) {
                require(!askedVideos[q.videoId],"duplicate question for video");
                askedVideos[q.videoId] = true;
                require(q.correctIndex>=0 && q.correctIndex<4,"correct index outside 4 choices");
                Set<String> unique = new HashSet<>(Arrays.asList(q.options));
                require(unique.size()==4,"duplicate answer options");
                if (q.isOrderQuestion) {
                    orderQuestions++;
                    require(q.prompt.contains("何番目"),"order question missing topic");
                    require(q.options[q.correctIndex].equals(positions[q.videoId]+"番目"),"wrong order question answer");
                } else {
                    contentQuestions++;
                }
            }
            require(orderQuestions==2 && contentQuestions==8,"question type balance invalid");
            require(game.answeredCount()==0 && game.correctCount()==0,"session should be empty");
            require(game.dopaScorePercent()==100,"no answers should produce 100 score");
            for(int i=0;i<10;i++){
                game.submitAnswer(i, game.questions[i].correctIndex);
                require(game.correctCount()==i+1,"correct answer scoring failed");
            }
            require(game.answeredCount()==10 && game.correctCount()==10,"perfect answer count failed");
            require(game.dopaScorePercent()==0,"perfect score should be zero");
        }
        require(permutations.size()>1100,"video shuffling seems broken");
        GameSession early = new GameSession(new Random(198));
        for(int i=0;i<3;i++) early.submitAnswer(i,early.questions[i].correctIndex);
        early.quitQuiz();
        require(early.answeredCount()==3,"quit must preserve prior answers");
        require(early.correctCount()==3,"quit must keep all earlier correct answers");
        require(early.overallAccuracyPercent()==30,"unanswered must count as incorrect");
        require(early.dopaScorePercent()==80,"quit penalty should add 10 points");
        boolean rejected=false;
        try {early.submitAnswer(3,0);} catch(IllegalStateException expected){rejected=true;}
        require(rejected,"should reject submissions after quit");
        GameSession zero = new GameSession(new Random(0));
        zero.quitQuiz();
        require(zero.dopaScorePercent()==100,"score should cap at 100");
        System.out.println("Java game engine: 1200 sessions, 8+2 questions, shuffle, order choices, perfect score, quit penalty PASSED");
    }
}
