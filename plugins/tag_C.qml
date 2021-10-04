import QtQuick 2.0
import MuseScore 3.0

MuseScore {
      menuPath: "Plugins.TagC"
      description: "Tag score as C instrument"
      version: "1.0"

      onRun: {
            console.log("Tagging as C")
            
            if (!curScore)
                  Qt.quit();

            // insert instrument name on first note
            var cursor = curScore.newCursor();
            cursor.staffIdx = 0;
            cursor.voice = 0;
            cursor.rewind(Cursor.SCORE_START);
            
            var text = newElement(Element.INSTRUMENT_CHANGE);
            text.autoplace = false;
            text.placement = Placement.ABOVE;
            text.text = "C Instrument";
            text.fontSize = 14;
            text.sizeSpatiumDependent = false;
            cursor.add(text);
            // offsets must be done AFTER adding
            text.offsetX = -8;
            text.offsetY = -8;

            Qt.quit();
      }
}
