import jp.example.dopagaki.GameSession;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Random;
import java.util.Set;

/** Pure Java tests (without Android SDK). Run tests/run_tests.sh. */
public final class GameSessionTest {
    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        require(GameSession.VIDEO_POOL_COUNT == 20, "20 story candidates");
        require(GameSession.CONTENT_QUESTION_COUNT == 10, "all ten are story questions");
        Set<String> pickedSets = new HashSet<>();
        boolean[] seenAcrossTrials = new boolean[20];
        int[] hits = new int[20];
        for (int seed=0; seed<2000; seed++) {
            GameSession s=new GameSession(new Random(seed));
            require(s.videoOrder.length==10 && s.questions.length==10, "10 clips / 10 questions");
            boolean[] seen=new boolean[20];
            for (int id:s.videoOrder) {
                require(id>=0 && id<20 && !seen[id], "selected clips must be unique");
                seen[id]=true;seenAcrossTrials[id]=true;
            }
            int[] sorted=s.videoOrder.clone();Arrays.sort(sorted);
            pickedSets.add(Arrays.toString(sorted));
            boolean[] asked=new boolean[20];
            for (GameSession.QuizQuestion q:s.questions) {
                require(seen[q.videoId] && !asked[q.videoId], "one question per viewed clip");
                asked[q.videoId]=true;hits[q.videoId]++;
                require(q.correctIndex>=0 && q.correctIndex<4, "valid answer index");
                require(q.options.length==4 && new HashSet<>(Arrays.asList(q.options)).size()==4, "four distinct choices");
                require(!q.prompt.matches(".*(何色|何枚|何本|何番目|何個).*"),"no color/count/order trivia");
                require(q.explanation.length()>8, "explanation exists");
            }
            for(int i=0;i<10;i++)s.submitAnswer(i,s.questions[i].correctIndex);
            require(s.correctCount()==10 && s.dopaScorePercent()==0,"perfect score");
        }
        require(pickedSets.size()>1000,"random selection must vary");
        for(int i=0;i<20;i++) require(seenAcrossTrials[i] && hits[i]>100,"story must be selectable");
        GameSession early=new GameSession(new Random(123));
        for(int i=0;i<3;i++)early.submitAnswer(i,early.questions[i].correctIndex);
        early.quitQuiz();
        require(early.answeredCount()==3 && early.dopaScorePercent()==80,"quit penalty");
        boolean rejected=false;
        try{early.submitAnswer(3,0);}catch(IllegalStateException expected){rejected=true;}
        require(rejected,"no answers after quit");
        System.out.println("Java: 2000 sessions, 20 picture-book clips, 10 story questions, scores PASS");
    }
}
