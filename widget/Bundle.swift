import WidgetKit
import SwiftUI

@main
struct MediaStaffWidgets: WidgetBundle {
    var body: some Widget {
        ShareTrackingWidget()
        ProgramTodayWidget()
        ProgramWeekWidget()
        NextMatchWidget()
        BirthdaysWidget()
    }
}
