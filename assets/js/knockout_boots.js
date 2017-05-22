ko.bindingHandlers.popover = {
    init: function(element, valueAccessor){
        var local = ko.utils.unwrapObservable(valueAccessor()),
            options = {},
            $elem = $(element),
            popoverEvent = 'click',
            popoverAction = 'show';

        ko.utils.extend(options, ko.bindingHandlers.popover.options);
        ko.utils.extend(options, local);

        if (options.trigger === 'hover') {
            popoverEvent = 'mouseenter mouseleave';
        } else if (options.trigger === 'focus') {
            popoverEvent = 'focus blur';
        }

        if(options.trigger !== 'click'){
            popoverAction = 'toggle';
        }

        $elem.on(popoverEvent, function(evt){
            if(popoverEvent === 'click'){
                evt.preventDefault();
            }
            $elem.popover(options).popover(popoverAction);

            var $popover = $elem.next();
            $popover.find('[data-dismiss="popover"]').on('click', function(){
                $elem.popover('hide');
            });
        });
    },

    options: {
        animation: true,
        html: true,
        placement: 'right',
        selector: false,
        trigger: 'manual',
        title: '',
        content: '',
        delay: 0,
        container: false
    }
};

ko.bindingHandlers.bootstrapswitch = {
    init: function(element, valueAccessor){
        var local = ko.utils.unwrapObservable(valueAccessor()),
            options = {},
            $elem = $(element);

	ko.utils.extend(options, ko.bindingHandlers.popover.options);
        ko.utils.extend(options, local);

        $elem.bootstrapSwitch(options);
    },

    options: {
        size: null,
        animate: true,
        disabled: false,
        readonly: false,
        onColor: "primary",
        offColor: "default",
        onText: "ON",
        offText: "OFF",
        labelText: "&nbsp;",
        onInit: function() {},
        onSwitchChange: function() {}
    }
};
