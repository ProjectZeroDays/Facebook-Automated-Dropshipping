package com.authenticated.dropship;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showDisclaimer();
    }
    private void showDisclaimer() {
        new AlertDialog.Builder(this)
            .setTitle("LEGAL DISCLAIMER — RESTRICTED USE")
            .setMessage(getString(R.string.disclaimer_text))
            .setCancelable(false)
            .setPositiveButton("I Understand — Proceed", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface d, int id) {
                    openWebView();
                }
            })
            .setNegativeButton("Exit", new DialogInterface.OnClickListener() {
                public void onClick(DialogInterface d, int id) {
                    finish();
                }
            })
            .show();
    }
    private void openWebView() {
        setContentView(R.layout.activity_main);
        webView = findViewById(R.id.webview);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        String url = getString(R.string.dashboard_url);
        webView.loadUrl(url);
    }
}
