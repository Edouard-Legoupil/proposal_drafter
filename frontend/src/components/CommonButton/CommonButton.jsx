import './CommonButton.css'

export default function CommonButton(props) {
        return <button
                type={props?.type ?? "button"}
                className={`CommonButton ${props?.loading ? "loading" : ""} ${props?.className ?? ""}`}
                onClick={props?.onClick}
                disabled={props?.disabled || props?.loading}
                style={props?.style}
                data-testid={props['data-testid']}
        >
                {props?.loading ?
                        <>
                                <span className='submitButtonSpinner' />
                                {props?.loadingLabel ?? props?.label}
                        </>
                        :
                        <>
                                {props?.icon ? <img className='Dashboard_top_createNewButton_icon' src={props?.icon} alt="Button Icon" /> : ""}
                                {props?.label}
                        </>
                }
        </button>
}
