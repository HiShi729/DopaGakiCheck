package jp.example.dopagaki;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.res.Configuration;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.VideoView;

import java.util.Locale;

/**
 * DopaGaki Check: offline 10-of-20 silent picture-book story game.
 * This is entertainment, not a validated attention, addiction or medical assessment.
 * No network, analytics, advertising or dangerous permissions are used.
 */
public final class MainActivity extends Activity {
    private static final int CLIP_COUNT = GameSession.CLIP_COUNT;
    private static final int CLIP_DURATION_MS = 18_000;
    private static final int START = 0;
    private static final int FEED = 1;
    private static final int QUIZ = 2;
    private static final int RESULT = 3;

    private static final int DARK = Color.rgb(10, 14, 20);
    private static final int SURFACE = Color.rgb(22, 28, 36);
    private static final int SURFACE_2 = Color.rgb(31, 39, 47);
    private static final int WHITE = Color.rgb(247, 249, 247);
    private static final int MUTED = Color.rgb(156, 169, 172);
    private static final int ACCENT = Color.rgb(195, 245, 98);
    private static final int BORDER = Color.rgb(56, 66, 70);

    private static final int[] VIDEOS = {
        R.raw.clip01, R.raw.clip02, R.raw.clip03, R.raw.clip04, R.raw.clip05,
        R.raw.clip06, R.raw.clip07, R.raw.clip08, R.raw.clip09, R.raw.clip10,
        R.raw.clip11, R.raw.clip12, R.raw.clip13, R.raw.clip14, R.raw.clip15,
        R.raw.clip16, R.raw.clip17, R.raw.clip18, R.raw.clip19, R.raw.clip20
    };

    private static final int[] STILLS = {
        R.drawable.still01, R.drawable.still02, R.drawable.still03,
        R.drawable.still04, R.drawable.still05, R.drawable.still06,
        R.drawable.still07, R.drawable.still08, R.drawable.still09, R.drawable.still10,
        R.drawable.still11, R.drawable.still12, R.drawable.still13, R.drawable.still14, R.drawable.still15,
        R.drawable.still16, R.drawable.still17, R.drawable.still18, R.drawable.still19, R.drawable.still20
    };

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final boolean[] completed = new boolean[CLIP_COUNT];
    private final boolean[] skipped = new boolean[CLIP_COUNT];
    private final int[] playTimeMs = new int[CLIP_COUNT];
    private GameSession session;

    private FrameLayout page;
    private VideoView videoView;
    private TextView videoTimer;
    private TextView pauseBadge;
    private int mode = START;
    private int clipIndex = 0;
    private int questionIndex = 0;
    private int selectedOption = -1;
    private boolean userPaused = false;
    private int pauseCount = 0;
    private int pendingSeekPositionMs = 0;
    private boolean restorePaused = false;

    private final Runnable timerTick = new Runnable() {
        @Override public void run() {
            if (mode != FEED || videoView == null) return;
            int current = Math.max(0, videoView.getCurrentPosition());
            if (videoTimer != null) {
                int secondsLeft = Math.max(0, (CLIP_DURATION_MS - current + 999) / 1_000);
                videoTimer.setText(String.format(Locale.JAPAN, "00:%02d", secondsLeft));
            }
            handler.postDelayed(this, 250);
        }
    };

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        immersive();
        reset();
        renderIntro();
    }

    private void immersive() {
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) immersive();
    }

    @Override protected void onPause() {
        super.onPause();
        if (mode == FEED && videoView != null && videoView.isPlaying()) {
            videoView.pause();
            userPaused = true;
            if (pauseBadge != null) pauseBadge.setVisibility(View.VISIBLE);
        }
    }

    @Override public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // The Android manifest lets us handle rotations without resetting the quiz.
        if (mode == FEED) {
            pendingSeekPositionMs = videoView == null ? 0 : videoView.getCurrentPosition();
            restorePaused = userPaused;
            renderFeed();
        } else if (mode == QUIZ) {
            renderQuiz();
        } else if (mode == RESULT) {
            renderResult();
        } else {
            renderIntro();
        }
    }

    @Override protected void onDestroy() {
        detachVideo();
        super.onDestroy();
    }

    @Override public void onBackPressed() {
        if (mode == START || mode == RESULT) {
            super.onBackPressed();
            return;
        }
        if (mode == QUIZ) {
            showQuitQuizDialog();
            return;
        }
        new AlertDialog.Builder(this)
            .setTitle("テストを終了しますか？")
            .setMessage("途中までの回答と視聴状況は破棄されます。")
            .setNegativeButton("続ける", (dialog, which) -> {
                immersive();
            })
            .setPositiveButton("終了する", (dialog, which) -> {
                detachVideo();
                reset();
                renderIntro();
            })
            .show();
    }

    private void reset() {
        session = new GameSession(); // fresh independent shuffle on every new attempt
        clipIndex = 0;
        questionIndex = 0;
        selectedOption = -1;
        userPaused = false;
        pauseCount = 0;
        pendingSeekPositionMs = 0;
        restorePaused = false;
        for (int i = 0; i < CLIP_COUNT; i++) {
            completed[i] = false;
            skipped[i] = false;
            playTimeMs[i] = 0;
        }
    }

    private void detachVideo() {
        handler.removeCallbacks(timerTick);
        if (videoView != null) {
            videoView.setOnCompletionListener(null);
            videoView.setOnPreparedListener(null);
            videoView.setOnErrorListener(null);
            videoView.stopPlayback();
            videoView = null;
        }
        videoTimer = null;
        pauseBadge = null;
    }

    private void setPage(FrameLayout root, int newMode) {
        detachVideo();
        mode = newMode;
        page = root;
        setContentView(root);
        immersive();
    }

    private FrameLayout darkPage() {
        FrameLayout frame = new FrameLayout(this);
        frame.setBackground(gradient(DARK, Color.rgb(18, 30, 34), 0));
        return frame;
    }

    private void renderIntro() {
        FrameLayout screen = darkPage();
        screen.addView(new IntroArt(this), new FrameLayout.LayoutParams(-1, -1));
        ScrollView scroll = makeScroll();
        LinearLayout content = stack(0);
        content.setPadding(contentInsetDp(18, 660), dp(26), contentInsetDp(18, 660), dp(20));
        content.setGravity(Gravity.CENTER_VERTICAL);
        content.setMinimumHeight(getResources().getDisplayMetrics().heightPixels - dp(36));

        TextView kicker = text("DOPA  /  MEMORY EXPERIMENT", 12, ACCENT, true);
        content.addView(kicker);
        gap(content, 25);
        TextView headline = text("退屈を、\n覚えていますか。", 41, WHITE, true);
        headline.setLineSpacing(dp(5), 1.0f);
        content.addView(headline);
        gap(content, 18);
        TextView subtitle = text("文字のない物語20本から毎回10本。\n全編を視聴すると約3分です。", 15, MUTED, false);
        subtitle.setLineSpacing(dp(5), 1.0f);
        content.addView(subtitle);
        gap(content, 18);

        LinearLayout quizNotice = stack(0);
        quizNotice.setPadding(dp(17), dp(14), dp(17), dp(14));
        quizNotice.setBackground(round(SURFACE_2, 15));
        TextView noticeTitle = text("このあと、クイズを出します。", 18, ACCENT, true);
        quizNotice.addView(noticeTitle);
        gap(quizNotice, 6);
        TextView noticeBody = text("10本の物語の結末や出来事について4択で10問出題します。\nスキップした動画も出題対象です。", 14, WHITE, false);
        noticeBody.setLineSpacing(dp(3), 1.0f);
        quizNotice.addView(noticeBody);
        content.addView(quizNotice, new LinearLayout.LayoutParams(-1, -2));
        gap(content, 24);
        LinearLayout statRow = new LinearLayout(this);
        statRow.setOrientation(LinearLayout.HORIZONTAL);
        addStat(statRow, "10", "VIDEOS");
        addStat(statRow, "180", "SECONDS");
        addStat(statRow, "10", "QUESTIONS");
        content.addView(statRow);
        gap(content, 27);
        TextView start = actionButton("テストをはじめる  →", true);
        content.addView(start, new LinearLayout.LayoutParams(-1, dp(62)));
        start.setOnClickListener(v -> renderFeed());
        gap(content, 18);
        TextView info = text("上にスワイプしてスキップできます。\nクイズも途中終了できます。音声・通信は不要です。", 13, MUTED, false);
        info.setGravity(Gravity.CENTER);
        info.setLineSpacing(dp(3), 1f);
        content.addView(info);
        gap(content, 20);
        TextView disclaimer = text("※ 本アプリの「ドパガキ度」は遊び用のスコアです。\n依存症や集中力を医学的に判定するものではありません。", 11, MUTED, false);
        disclaimer.setGravity(Gravity.CENTER);
        disclaimer.setLineSpacing(dp(3), 1f);
        content.addView(disclaimer);
        scroll.addView(content, new ScrollView.LayoutParams(-1, -2));
        screen.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        setPage(screen, START);
    }

    private void renderFeed() {
        if (clipIndex >= CLIP_COUNT) {
            questionIndex = 0;
            selectedOption = -1;
            renderQuiz();
            return;
        }
        FrameLayout screen = new FrameLayout(this);
        screen.setBackgroundColor(DARK);
        setPage(screen, FEED);
        userPaused = restorePaused;
        restorePaused = false;
        FrameLayout viewport = new FrameLayout(this);
        viewport.setBackgroundColor(Color.BLACK);
        if (isTablet()) {
            int w = getResources().getDisplayMetrics().widthPixels;
            int h = getResources().getDisplayMetrics().heightPixels;
            int portraitHeight = Math.min(h, (int) (w * 16f / 9f));
            int portraitWidth = Math.min(w, (int) (portraitHeight * 9f / 16f));
            screen.addView(viewport, new FrameLayout.LayoutParams(portraitWidth, portraitHeight, Gravity.CENTER));
        } else {
            screen.addView(viewport, new FrameLayout.LayoutParams(-1, -1));
        }

        videoView = new VideoView(this);
        // Do not apply an opaque background to a VideoView: it may cover its video surface.
        videoView.setBackgroundColor(Color.TRANSPARENT);
        videoView.setKeepScreenOn(true);
        viewport.addView(videoView, new FrameLayout.LayoutParams(-1, -1));
        Uri uri = Uri.parse("android.resource://" + getPackageName() + "/" + VIDEOS[session.videoOrder[clipIndex]]);
        videoView.setOnPreparedListener(mp -> {
            mp.setLooping(false);
            if (pendingSeekPositionMs > 0) {
                int seek = pendingSeekPositionMs;
                pendingSeekPositionMs = 0;
                videoView.seekTo(seek);
            }
            if (mode == FEED && !userPaused) videoView.start();
            if (pauseBadge != null) pauseBadge.setVisibility(userPaused ? View.VISIBLE : View.GONE);
        });
        videoView.setOnCompletionListener(mp -> {
            if (mode != FEED) return;
            completed[clipIndex] = true;
            playTimeMs[clipIndex] = CLIP_DURATION_MS;
            pendingSeekPositionMs = 0;
            clipIndex++;
            renderFeed();
        });
        videoView.setOnErrorListener((mp, what, extra) -> {
            if (mode == FEED) {
                Toast.makeText(this, "この動画を再生できませんでした。次へ進みます。", Toast.LENGTH_SHORT).show();
                advanceBySkipping();
            }
            return true;
        });

        // Touch capture layer: swipe up to skip, tap to pause/play, swipe down does not rewind.
        View touchLayer = new View(this);
        viewport.addView(touchLayer, new FrameLayout.LayoutParams(-1, -1));
        touchLayer.setOnTouchListener(new View.OnTouchListener() {
            private float downX, downY;
            @Override public boolean onTouch(View v, MotionEvent event) {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downX = event.getX();
                        downY = event.getY();
                        return true;
                    case MotionEvent.ACTION_UP:
                        float dx = event.getX() - downX;
                        float dy = event.getY() - downY;
                        if (Math.abs(dy) > dp(74) && Math.abs(dy) > Math.abs(dx) * 1.2f) {
                            if (dy < 0) advanceBySkipping();
                            else Toast.makeText(MainActivity.this, "前の動画には戻れません", Toast.LENGTH_SHORT).show();
                        } else if (Math.abs(dx) < dp(35) && Math.abs(dy) < dp(35)) {
                            togglePlayback();
                        }
                        return true;
                    default:
                        return true;
                }
            }
        });

        View topShade = new View(this);
        topShade.setBackground(gradient(Color.argb(205, 0, 0, 0), Color.TRANSPARENT, 0));
        FrameLayout.LayoutParams topShadeLp = new FrameLayout.LayoutParams(-1, dp(190), Gravity.TOP);
        viewport.addView(topShade, topShadeLp);
        View bottomShade = new View(this);
        bottomShade.setBackground(gradient(Color.TRANSPARENT, Color.argb(225, 0, 0, 0), 0));
        viewport.addView(bottomShade, new FrameLayout.LayoutParams(-1, dp(117), Gravity.BOTTOM));

        LinearLayout top = stack(0);
        top.setPadding(dp(22), dp(34), dp(22), 0);
        LinearLayout topRow = new LinearLayout(this);
        topRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView brand = text("DOPA / FEED", 14, WHITE, true);
        topRow.addView(brand, new LinearLayout.LayoutParams(0, -2, 1));
        TextView count = text(String.format(Locale.JAPAN, "%02d / 10", clipIndex + 1), 16, WHITE, true);
        topRow.addView(count);
        top.addView(topRow);
        gap(top, 18);
        LinearLayout segments = new LinearLayout(this);
        segments.setOrientation(LinearLayout.HORIZONTAL);
        for (int i = 0; i < CLIP_COUNT; i++) {
            View part = new View(this);
            part.setBackground(round(i <= clipIndex ? ACCENT : Color.argb(115, 240, 240, 240), 3));
            LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(0, dp(4), 1);
            sp.setMargins(0, 0, i == CLIP_COUNT - 1 ? 0 : dp(4), 0);
            segments.addView(part, sp);
        }
        top.addView(segments);
        gap(top, 9);
        top.addView(text("上スワイプで次へ・タップで一時停止", 11, WHITE, false));
        viewport.addView(top, new FrameLayout.LayoutParams(-1, -2, Gravity.TOP));

        pauseBadge = text("一時停止  ·  タップで再開", 16, WHITE, true);
        pauseBadge.setGravity(Gravity.CENTER);
        pauseBadge.setBackground(round(Color.argb(196, 0, 0, 0), 18));
        pauseBadge.setPadding(dp(18), dp(12), dp(18), dp(12));
        pauseBadge.setVisibility(View.GONE);
        viewport.addView(pauseBadge, new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER));

        LinearLayout bottom = stack(0);
        bottom.setPadding(dp(23), 0, dp(22), dp(20));
        LinearLayout actionRow = new LinearLayout(this);
        actionRow.setGravity(Gravity.CENTER_VERTICAL);
        videoTimer = text("00:18", 15, WHITE, true);
        actionRow.addView(videoTimer, new LinearLayout.LayoutParams(0, -2, 1));
        TextView skip = text("スキップ  ↑", 15, WHITE, true);
        skip.setPadding(dp(17), dp(11), dp(17), dp(11));
        skip.setGravity(Gravity.CENTER);
        skip.setBackground(round(Color.argb(168, 0, 0, 0), 40));
        actionRow.addView(skip);
        skip.setOnClickListener(v -> advanceBySkipping());
        bottom.addView(actionRow);
        viewport.addView(bottom, new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM));
        videoView.setVideoURI(uri);
        videoView.requestFocus();
        handler.post(timerTick);
    }

    private void advanceBySkipping() {
        if (mode != FEED || clipIndex >= CLIP_COUNT) return;
        int current = videoView == null ? 0 : videoView.getCurrentPosition();
        playTimeMs[clipIndex] = Math.max(0, Math.min(CLIP_DURATION_MS, current));
        skipped[clipIndex] = true;
        pendingSeekPositionMs = 0;
        clipIndex++;
        renderFeed();
    }

    private void togglePlayback() {
        if (mode != FEED || videoView == null) return;
        if (videoView.isPlaying()) {
            videoView.pause();
            pauseCount++;
            userPaused = true;
        } else {
            userPaused = false;
            videoView.start();
        }
        if (pauseBadge != null) pauseBadge.setVisibility(userPaused ? View.VISIBLE : View.GONE);
    }

    private LinearLayout makeQuizOption(GameSession.QuizQuestion question, int choice, boolean compact) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(11), dp(5), dp(11), dp(5));
        boolean chosen = selectedOption == choice;
        GradientDrawable bg = round(chosen ? Color.rgb(41, 61, 43) : SURFACE, 13);
        bg.setStroke(dp(1), chosen ? ACCENT : BORDER);
        row.setBackground(bg);
        TextView letter = text(String.valueOf((char) ('A' + choice)), 14, chosen ? ACCENT : MUTED, true);
        letter.setGravity(Gravity.CENTER);
        row.addView(letter, new LinearLayout.LayoutParams(dp(32), -2));
        TextView optionText = text(question.options[choice], compact ? 14 : 16, WHITE, chosen);
        optionText.setMaxLines(5);
        row.addView(optionText, new LinearLayout.LayoutParams(0, -2, 1));
        if (chosen) row.addView(text("●", 16, ACCENT, true));
        row.setOnClickListener(v -> {
            selectedOption = choice;
            renderQuiz();
        });
        return row;
    }

    private void renderQuiz() {
        FrameLayout screen = darkPage();
        int usableDp = (int)(getResources().getDisplayMetrics().heightPixels / getResources().getDisplayMetrics().density);
        boolean compact = usableDp < 760;
        boolean tablet = isTablet();
        LinearLayout content = stack(0);
        if (tablet) content.setGravity(Gravity.CENTER_VERTICAL);
        int sidePadding = contentInsetDp(19, 740);
        content.setPadding(sidePadding, dp(compact ? 15 : 28), sidePadding, dp(12));
        LinearLayout quizHeader = new LinearLayout(this);
        quizHeader.setGravity(Gravity.CENTER_VERTICAL);
        quizHeader.addView(text("DOPA / QUIZ", 13, ACCENT, true),
            new LinearLayout.LayoutParams(0, -2, 1));
        TextView quitTop = text("途中終了  ×", 13, MUTED, true);
        quitTop.setPadding(dp(12), dp(8), 0, dp(8));
        quizHeader.addView(quitTop);
        quitTop.setOnClickListener(v -> showQuitQuizDialog());
        content.addView(quizHeader);
        gap(content, compact ? 8 : 14);

        TextView counter = text(String.format(Locale.JAPAN, "QUESTION  %02d / 10", questionIndex + 1), 13, MUTED, true);
        content.addView(counter);
        gap(content, 7);
        LinearLayout progress = new LinearLayout(this);
        for (int i = 0; i < CLIP_COUNT; i++) {
            View part = new View(this);
            part.setBackground(round(i <= questionIndex ? ACCENT : BORDER, 3));
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(5), 1);
            p.setMargins(0, 0, i == CLIP_COUNT - 1 ? 0 : dp(4), 0);
            progress.addView(part, p);
        }
        content.addView(progress);
        gap(content, compact ? 13 : 22);
        GameSession.QuizQuestion question = session.questions[questionIndex];
        TextView context = text("冒頭のシーンを見て、この物語を思い出してください", 13, ACCENT, true);
        content.addView(context);
        gap(content, 6);
        // Show an original still from 0s for every story question; never reveal the outcome.
        LinearLayout thumbnailRow = new LinearLayout(this);
        thumbnailRow.setGravity(Gravity.CENTER);
        ImageView still = new ImageView(this);
        still.setImageResource(STILLS[question.videoId]);
        still.setScaleType(ImageView.ScaleType.CENTER_CROP);
        still.setContentDescription("この物語の冒頭場面。結末は写っていません");
        still.setBackground(round(SURFACE_2, 13));
        still.setClipToOutline(true);
        thumbnailRow.addView(still, new LinearLayout.LayoutParams(
            dp(compact ? 104 : 126), dp(compact ? 142 : 176)));
        content.addView(thumbnailRow, new LinearLayout.LayoutParams(-1, -2));
        gap(content, compact ? 8 : 12);
        TextView title = text(question.prompt, compact ? 21 : 25, WHITE, true);
        title.setLineSpacing(dp(6), 1f);
        content.addView(title);
        gap(content, compact ? 12 : 20);

        if (tablet) {
            // Two columns keep four choices above the bottom edge in landscape.
            for (int rowNumber = 0; rowNumber < 2; rowNumber++) {
                LinearLayout choicesRow = new LinearLayout(this);
                choicesRow.setOrientation(LinearLayout.HORIZONTAL);
                for (int column = 0; column < 2; column++) {
                    int choice = rowNumber * 2 + column;
                    LinearLayout option = makeQuizOption(question, choice, compact);
                    option.setMinimumHeight(dp(compact ? 64 : 72));
                    LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -2, 1);
                    p.setMargins(0, 0, column == 0 ? dp(8) : 0, 0);
                    choicesRow.addView(option, p);
                }
                LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(-1, -2);
                rp.setMargins(0, 0, 0, dp(9));
                content.addView(choicesRow, rp);
            }
        } else {
            for (int i = 0; i < question.options.length; i++) {
                LinearLayout option = makeQuizOption(question, i, compact);
                option.setMinimumHeight(dp(compact ? 52 : 62));
                LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(-1, -2);
                rp.setMargins(0, 0, 0, dp(compact ? 6 : 9));
                content.addView(option, rp);
            }
        }
        gap(content, compact ? 7 : 11);
        TextView next = actionButton(questionIndex == CLIP_COUNT - 1 ? "結果を見る  →" : "回答を確定して次へ  →", selectedOption >= 0);
        next.setAlpha(selectedOption >= 0 ? 1f : 0.48f);
        content.addView(next, new LinearLayout.LayoutParams(-1, dp(compact ? 48 : 54)));
        next.setOnClickListener(v -> {
            if (selectedOption < 0) return;
            session.submitAnswer(questionIndex, selectedOption);
            selectedOption = -1;
            questionIndex++;
            if (questionIndex == CLIP_COUNT) renderResult();
            else renderQuiz();
        });
        // Always allow scrolling: large font settings and small phones must not clip answers.
        ScrollView scroll = makeScroll();
        if (tablet) content.setMinimumHeight(getResources().getDisplayMetrics().heightPixels);
        scroll.addView(content, new ScrollView.LayoutParams(-1, -2));
        screen.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        setPage(screen, QUIZ);
    }

    private void showQuitQuizDialog() {
        if (mode != QUIZ) return;
        new AlertDialog.Builder(this)
            .setTitle("ここでクイズをやめますか？")
            .setMessage("現在の確定回答: " + session.answeredCount() + "/10問\n"
                + "未回答は不正解扱いです。途中終了するとドパガキ度に10ポイント加算されます（最大100%）。")
            .setNegativeButton("クイズに戻る", (dialog, which) -> immersive())
            .setPositiveButton("終了して採点", (dialog, which) -> {
                session.quitQuiz();
                renderResult();
            })
            .show();
    }

    private int skippedCount() {
        int n = 0;
        for (boolean value : skipped) if (value) n++;
        return n;
    }

    private int completedCount() {
        int n = 0;
        for (boolean value : completed) if (value) n++;
        return n;
    }

    private int totalWatchedSeconds() {
        long milliseconds = 0;
        for (int t : playTimeMs) milliseconds += t;
        return (int) (milliseconds / 1000L);
    }

    private String formatDuration(int seconds) {
        return String.format(Locale.JAPAN, "%02d:%02d", seconds / 60, seconds % 60);
    }

    private String resultLabel(int score) {
        if (score <= 20) return "記憶力ばっちり";
        if (score <= 40) return "じっくり観察タイプ";
        if (score <= 60) return "なんとなくスワイパー";
        if (score <= 80) return "刺激が恋しいタイプ";
        return "高速スワイパー";
    }

    private String shareText() {
        int correct = session.correctCount();
        int dopaScore = session.dopaScorePercent();
        return "ドパガキ診断（エンタメ）\n"
            + "ドパガキ度: " + dopaScore + "%\n"
            + "クイズ: " + correct + "/10問正解（" + session.answeredCount() + "/10問回答）\n"
            + "クイズ: " + (session.finishedEarly ? "途中終了" : "完走") + "\n"
            + "動画スキップ: " + skippedCount() + "/10本\n"
            + "実際の動画視聴時間（概算）: " + formatDuration(totalWatchedSeconds()) + "\n"
            + "全動画視聴時: 03:00\n"
            + "※医学・心理学的な診断ではありません。";
    }

    private void renderResult() {
        int correct = session.correctCount();
        int percentage = session.overallAccuracyPercent();
        int score = session.dopaScorePercent();
        FrameLayout screen = darkPage();
        ScrollView scroll = makeScroll();
        LinearLayout content = stack(0);
        int resultInset = contentInsetDp(25, 740);
        content.setPadding(resultInset, dp(35), resultInset, dp(42));

        content.addView(text("DOPA / RESULT", 13, ACCENT, true));
        gap(content, 24);
        content.addView(text("診断結果", 33, WHITE, true));
        gap(content, 32);
        TextView scoreLabel = text("ドパガキ度（ゲーム内スコア）", 16, MUTED, false);
        content.addView(scoreLabel);
        gap(content, 8);
        LinearLayout scoreRow = new LinearLayout(this);
        scoreRow.setGravity(Gravity.BOTTOM);
        TextView big = text(String.valueOf(score), 100, ACCENT, true);
        scoreRow.addView(big);
        TextView percent = text("%", 37, ACCENT, true);
        LinearLayout.LayoutParams percentLp = new LinearLayout.LayoutParams(-2, -2);
        percentLp.setMargins(dp(7), 0, 0, dp(16));
        scoreRow.addView(percent, percentLp);
        content.addView(scoreRow);
        TextView type = text(resultLabel(score) + (session.finishedEarly ? " · クイズ途中終了" : ""), 21, WHITE, true);
        content.addView(type);
        gap(content, 24);
        View divider = new View(this);
        divider.setBackgroundColor(BORDER);
        content.addView(divider, new LinearLayout.LayoutParams(-1, dp(1)));
        gap(content, 25);

        LinearLayout stats = new LinearLayout(this);
        stats.setOrientation(LinearLayout.HORIZONTAL);
        stats.setGravity(Gravity.CENTER_VERTICAL);
        addStat(stats, correct + "/10", "正解数");
        addStat(stats, percentage + "%", "全10問の正答率");
        addStat(stats, skippedCount() + "/10", "スキップ");
        content.addView(stats);
        gap(content, 18);
        TextView details = text("クイズ: " + (session.finishedEarly ? "途中終了" : "10問完走")
            + "（回答 " + session.answeredCount() + "/10問）\n"
            + "動画を最後まで再生: " + completedCount() + "/10本\n"
            + "実際の動画視聴時間（概算）: " + formatDuration(totalWatchedSeconds()) + "\n"
            + "全動画を最後まで見た場合: 03:00\n"
            + "短縮時間（概算）: " + formatDuration(Math.max(0, 180 - totalWatchedSeconds())) + "\n"
            + "一時停止操作: " + pauseCount + "回", 13, MUTED, false);
        details.setLineSpacing(dp(6), 1f);
        content.addView(details);
        gap(content, 26);

        TextView disclaimer = text("ドパガキ度 = min(100, 100 − 正答率 + 途中終了なら10)。未回答は不正解です。この結果は物語の展開や結末を思い出すゲームの成績であり、途中終了の原因も判定できません。ドーパミン量、依存症、注意機能を評価する科学的な指標ではありません。", 13, MUTED, false);
        disclaimer.setLineSpacing(dp(5), 1f);
        content.addView(disclaimer);
        gap(content, 25);
        TextView share = actionButton("結果をシェア  ↗", true);
        content.addView(share, new LinearLayout.LayoutParams(-1, dp(60)));
        share.setOnClickListener(v -> {
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("text/plain");
            send.putExtra(Intent.EXTRA_TEXT, shareText());
            startActivity(Intent.createChooser(send, "結果を共有"));
        });
        gap(content, 11);
        TextView copy = actionButton("結果をコピー", false);
        content.addView(copy, new LinearLayout.LayoutParams(-1, dp(60)));
        copy.setOnClickListener(v -> {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) {
                clipboard.setPrimaryClip(ClipData.newPlainText("ドパガキ診断", shareText()));
                Toast.makeText(this, "コピーしました", Toast.LENGTH_SHORT).show();
            }
        });
        gap(content, 11);
        TextView replay = actionButton("もう一度チャレンジ", false);
        content.addView(replay, new LinearLayout.LayoutParams(-1, dp(60)));
        replay.setOnClickListener(v -> {
            reset();
            renderIntro();
        });
        gap(content, 40);
        content.addView(text("答え合わせ", 25, WHITE, true));
        gap(content, 18);

        for (int i = 0; i < CLIP_COUNT; i++) {
            GameSession.QuizQuestion q = session.questions[i];
            int response = session.answers[i];
            boolean unanswered = response < 0;
            boolean ok = !unanswered && response == q.correctIndex;
            LinearLayout review = stack(7);
            review.setPadding(dp(18), dp(16), dp(18), dp(16));
            GradientDrawable shape = round(SURFACE, 15);
            shape.setStroke(dp(1), BORDER);
            review.setBackground(shape);
            String status = unanswered ? "未回答" : (ok ? "正解" : "不正解");
            String category = "物語問題";
            TextView qHeader = text(String.format(Locale.JAPAN, "Q%02d  ·  %s · %s", i + 1, category, status),
                13, ok ? ACCENT : Color.rgb(241, 160, 153), true);
            review.addView(qHeader);
            review.addView(text(q.prompt, 16, WHITE, true));
            review.addView(text("あなたの回答: " + (unanswered ? "未回答" : q.options[response]), 13, MUTED, false));
            review.addView(text("正解: " + q.options[q.correctIndex], 13, WHITE, true));
            review.addView(text(q.explanation, 12, MUTED, false));
            LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(-1, -2);
            rp.setMargins(0, 0, 0, dp(12));
            content.addView(review, rp);
        }
        scroll.addView(content);
        screen.addView(scroll, new FrameLayout.LayoutParams(-1, -1));
        setPage(screen, RESULT);
    }

    // ---- View and style helpers, all using Android framework APIs only ----
    private boolean isTablet() {
        return getResources().getConfiguration().smallestScreenWidthDp >= 600;
    }

    /** Side margins that center content while allowing the phone to use its width. */
    private int contentInsetDp(int minimumDp, int maxContentWidthDp) {
        int currentWidthDp = getResources().getConfiguration().screenWidthDp;
        return dp(Math.max(minimumDp, (currentWidthDp - maxContentWidthDp) / 2));
    }

    private int dp(float x) {
        return (int) (x * getResources().getDisplayMetrics().density + .5f);
    }

    private TextView text(String value, int sp, int color, boolean bold) {
        TextView tv = new TextView(this);
        tv.setText(value);
        tv.setTextSize(sp);
        tv.setTextColor(color);
        tv.setIncludeFontPadding(false);
        tv.setGravity(Gravity.CENTER_VERTICAL);
        if (bold) tv.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
        return tv;
    }

    private LinearLayout stack(int gapDp) {
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        if (gapDp > 0) col.setPadding(0, dp(gapDp), 0, 0);
        return col;
    }

    private ScrollView makeScroll() {
        ScrollView s = new ScrollView(this);
        s.setFillViewport(true);
        s.setVerticalScrollBarEnabled(false);
        s.setPadding(0, 0, 0, 0);
        return s;
    }

    private void gap(LinearLayout col, int dpHeight) {
        col.addView(new View(this), new LinearLayout.LayoutParams(1, dp(dpHeight)));
    }

    private GradientDrawable round(int color, int cornerDp) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(cornerDp));
        return drawable;
    }

    private GradientDrawable gradient(int top, int bottom, int radiusDp) {
        GradientDrawable drawable = new GradientDrawable(
            GradientDrawable.Orientation.TOP_BOTTOM, new int[]{top, bottom});
        drawable.setCornerRadius(dp(radiusDp));
        return drawable;
    }

    private TextView actionButton(String title, boolean primary) {
        TextView button = text(title, 16, primary ? DARK : WHITE, true);
        button.setGravity(Gravity.CENTER);
        GradientDrawable bg = round(primary ? ACCENT : SURFACE_2, 16);
        if (!primary) bg.setStroke(dp(1), BORDER);
        button.setBackground(bg);
        button.setClickable(true);
        button.setFocusable(true);
        return button;
    }

    private void addStat(LinearLayout row, String number, String caption) {
        LinearLayout stat = stack(0);
        TextView val = text(number, 25, WHITE, true);
        val.setGravity(Gravity.CENTER);
        stat.addView(val);
        gap(stat, 7);
        TextView label = text(caption, 10, MUTED, true);
        label.setGravity(Gravity.CENTER);
        stat.addView(label);
        row.addView(stat, new LinearLayout.LayoutParams(0, -2, 1));
    }

    private static final class IntroArt extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        IntroArt(Context context) { super(context); }
        @Override protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float w = getWidth();
            float h = getHeight();
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1.8f * getResources().getDisplayMetrics().density);
            for (int i = 0; i < 4; i++) {
                paint.setColor(Color.argb(i == 0 ? 50 : 30, 195, 245, 98));
                float r = w * (.35f + i * .2f);
                canvas.drawCircle(w * .95f, h * .25f, r, paint);
            }
            paint.setStyle(Paint.Style.FILL);
        }
    }
}
