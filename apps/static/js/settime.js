document.addEventListener('DOMContentLoaded', (event) => {
    var currentTime = new Date();
    var currentHours = currentTime.getHours();
    var currentMinutes = currentTime.getMinutes();

    var hoursSelect = document.getElementById('hours');
    var minutesSelect = document.getElementById('minutes');
    var recepHoursSelect = document.getElementById('recep_hours');
    var recepMinutesSelect = document.getElementById('recep_minutes');

    for (var i = 0; i < hoursSelect.options.length; i++) {
        if (hoursSelect.options[i].value == currentHours) {
            hoursSelect.selectedIndex = i;
            break;
        }
    }

    for (var i = 0; i < minutesSelect.options.length; i++) {
        if (minutesSelect.options[i].value == currentMinutes) {
            minutesSelect.selectedIndex = i;
            break;
        }
    }

    for (var i = 0; i < recepHoursSelect.options.length; i++) {
        if (recepHoursSelect.options[i].value == currentHours) {
            recepHoursSelect.selectedIndex = i;
            break;
        }
    }

    for (var i = 0; i < recepMinutesSelect.options.length; i++) {
        if (recepMinutesSelect.options[i].value == currentMinutes) {
            recepMinutesSelect.selectedIndex = i;
            break;
        }
    }
});
