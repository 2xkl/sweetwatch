using Toybox.Application;
using Toybox.WatchUi;

class SweetWatchApp extends Application.AppBase {

    function initialize() {
        AppBase.initialize();
    }

    function getInitialView() as Array<Views or InputDelegates>? {
        return [new SweetWatchView()] as Array<Views or InputDelegates>;
    }
}
