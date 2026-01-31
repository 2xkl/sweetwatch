using Toybox.Graphics;
using Toybox.WatchUi;
using Toybox.Communications;

class SweetWatchView extends WatchUi.View {

    var _glucoseValue as String = "--";
    var _trend as String = "";

    function initialize() {
        View.initialize();
    }

    function onLayout(dc as Dc) as Void {
        // Layout setup
    }

    function onShow() as Void {
        fetchGlucose();
    }

    function onUpdate(dc as Dc) as Void {
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();

        // Draw glucose value
        dc.drawText(
            dc.getWidth() / 2,
            dc.getHeight() / 2 - 20,
            Graphics.FONT_NUMBER_HOT,
            _glucoseValue,
            Graphics.TEXT_JUSTIFY_CENTER
        );

        // Draw trend arrow
        dc.drawText(
            dc.getWidth() / 2,
            dc.getHeight() / 2 + 40,
            Graphics.FONT_MEDIUM,
            _trend,
            Graphics.TEXT_JUSTIFY_CENTER
        );
    }

    function fetchGlucose() as Void {
        Communications.makeWebRequest(
            "http://YOUR_SERVER:8000/api/v1/glucose/current",
            null,
            {:method => Communications.HTTP_REQUEST_METHOD_GET,
             :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON},
            method(:onReceive)
        );
    }

    function onReceive(responseCode as Number, data as Dictionary or Null) as Void {
        if (responseCode == 200 && data != null) {
            _glucoseValue = data["value"].toString();
            _trend = data["trend_arrow"] as String;
        } else {
            _glucoseValue = "ERR";
        }
        WatchUi.requestUpdate();
    }
}
