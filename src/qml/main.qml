import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root

    width: 400
    height: 300

    title: "Dossier"

    pageStack.initialPage: Kirigami.ScrollablePage {
        title: "Library"

		Kirigami.CardsListView {
			id: cardsView
			model: dossierModel
			delegate: dossierDelegate
		}

    }
}
