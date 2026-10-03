package com.narmanb.megamanxrecomp;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * First-launch ROM setup. No ROM is bundled with the APK.
 *
 * The native host changes cwd to getExternalFilesDir(null), so placing the
 * verified dump there as mmx.sfc lets its normal ROM resolver find it without
 * Android storage permissions or a desktop file-picker dependency.
 */
public final class SetupActivity extends Activity {
    private static final int REQUEST_PICK_ROM = 1001;
    private static final String ROM_NAME = "mmx.sfc";
    private static final String EXPECTED_SHA256 =
            "b8f70a6e7fb93819f79693578887e2c11e196bdf1ac6ddc7cb924b1ad0be2d32";

    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            installRuntimeAssets();
        } catch (Exception e) {
            showSetup("Couldn't install runtime assets: " + e.getMessage());
            return;
        }

        File rom = romFile();
        if (rom.isFile()) {
            try {
                if (EXPECTED_SHA256.equalsIgnoreCase(normalizedSha256(rom))) {
                    launchGame();
                    return;
                }
            } catch (Exception ignored) {
                // Fall through to the picker with a useful message.
            }
            showSetup("The saved ROM does not match Mega Man X (USA) (Rev 1). Select the correct .sfc/.smc file.");
            return;
        }

        showSetup("Select your legally obtained Mega Man X (USA) (Rev 1) ROM (.sfc or .smc).");
    }

    private void showSetup(String message) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        int pad = (int) (24 * getResources().getDisplayMetrics().density);
        root.setPadding(pad, pad, pad, pad);

        status = new TextView(this);
        status.setText(message);
        status.setGravity(Gravity.CENTER);
        root.addView(status);

        Button pick = new Button(this);
        pick.setText("Select ROM");
        pick.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("*/*");
            startActivityForResult(intent, REQUEST_PICK_ROM);
        });
        root.addView(pick);

        setContentView(root);
        goFullscreen();
    }

    private File appFilesDir() {
        File dir = getExternalFilesDir(null);
        if (dir == null) throw new IllegalStateException("Android external-files directory is unavailable");
        return dir;
    }

    private File romFile() {
        return new File(appFilesDir(), ROM_NAME);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_PICK_ROM || resultCode != RESULT_OK || data == null) return;

        Uri uri = data.getData();
        if (uri == null) return;

        try {
            copyAndVerifyRom(uri);
            launchGame();
        } catch (Exception e) {
            if (status != null) status.setText("That file is not the required Mega Man X (USA) (Rev 1) ROM. " + e.getMessage());
        }
    }

    private void copyAndVerifyRom(Uri uri) throws Exception {
        File dest = romFile();
        File tmp = new File(dest.getParentFile(), ROM_NAME + ".tmp");
        if (tmp.exists() && !tmp.delete()) throw new IllegalStateException("could not replace temporary ROM");

        try (InputStream in = getContentResolver().openInputStream(uri);
             OutputStream out = new FileOutputStream(tmp)) {
            if (in == null) throw new IllegalStateException("could not open selected file");
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        }

        String digest = normalizedSha256(tmp);
        if (!EXPECTED_SHA256.equalsIgnoreCase(digest)) {
            tmp.delete();
            throw new IllegalStateException("SHA-256 mismatch.");
        }

        if (dest.exists() && !dest.delete()) {
            tmp.delete();
            throw new IllegalStateException("could not replace the previous ROM");
        }
        if (!tmp.renameTo(dest)) {
            tmp.delete();
            throw new IllegalStateException("could not finalize the ROM copy");
        }
    }

    /**
     * Upstream accepts both raw SFC dumps and SMC files with a 512-byte copier
     * header. Hash the logical ROM bytes exactly the same way.
     */
    private static String normalizedSha256(File file) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        long size = file.length();
        boolean hasCopierHeader = (size & 0x7fffL) == 512L;

        try (FileInputStream in = new FileInputStream(file)) {
            if (hasCopierHeader) {
                long remaining = 512;
                while (remaining > 0) {
                    long skipped = in.skip(remaining);
                    if (skipped <= 0) throw new IllegalStateException("could not skip SMC header");
                    remaining -= skipped;
                }
            }
            byte[] buf = new byte[64 * 1024];
            int n;
            while ((n = in.read(buf)) > 0) md.update(buf, 0, n);
        }

        StringBuilder hex = new StringBuilder(64);
        for (byte b : md.digest()) hex.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return hex.toString();
    }

    private void installRuntimeAssets() throws Exception {
        File root = appFilesDir();
        copyAssetTree(getAssets(), "assets", new File(root, "assets"));
        copyAssetTree(getAssets(), "mods", new File(root, "mods"));
    }

    private static void copyAssetTree(AssetManager am, String assetPath, File dest) throws Exception {
        String[] children = am.list(assetPath);
        if (children == null) throw new IllegalStateException("could not list APK asset " + assetPath);

        if (children.length == 0) {
            File parent = dest.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs())
                throw new IllegalStateException("could not create " + parent);
            try (InputStream in = am.open(assetPath);
                 OutputStream out = new FileOutputStream(dest)) {
                byte[] buf = new byte[32 * 1024];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            }
            return;
        }

        if (!dest.exists() && !dest.mkdirs())
            throw new IllegalStateException("could not create " + dest);
        for (String child : children) {
            copyAssetTree(am, assetPath + "/" + child, new File(dest, child));
        }
    }

    private void launchGame() {
        startActivity(new Intent(this, MainActivity.class));
        finish();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) goFullscreen();
    }

    private void goFullscreen() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }
}
